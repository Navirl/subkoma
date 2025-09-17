import argparse
import json
import sys
import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from backend.data_models import Keypoint, FrameData, AnalysisResult
    from backend.calculations import (
        calculate_displacement, calculate_velocity, calculate_acceleration,
        calculate_direction_change, calculate_pose_change, calculate_motion_intensity_score
    )
    from backend.timing_logic import TimingLogicProcessor, MotionState
except ImportError:
    # When running directly from backend directory
    from data_models import Keypoint, FrameData, AnalysisResult
    from calculations import (
        calculate_displacement, calculate_velocity, calculate_acceleration,
        calculate_direction_change, calculate_pose_change, calculate_motion_intensity_score
    )
    from timing_logic import TimingLogicProcessor, MotionState


def extract_keypoints_from_frame(frame: np.ndarray, pose_detector) -> List[Keypoint]:
    """Extract keypoints from a single frame using MediaPipe."""
    # Convert BGR to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process the frame
    results = pose_detector.process(rgb_frame)
    
    keypoints = []
    if results.pose_landmarks:
        # Extract landmark coordinates
        for i, landmark in enumerate(results.pose_landmarks.landmark):
            # Convert normalized coordinates to pixel coordinates
            h, w, _ = frame.shape
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            
            # Only include visible landmarks (visibility > 0.5)
            if landmark.visibility > 0.5:
                keypoints.append(Keypoint(x=x, y=y, name=f"landmark_{i}"))
    
    return keypoints


def process_video_pipeline(input_path: str, output_path: str, config: Dict[str, Any]) -> AnalysisResult:
    """Process video through the complete pipeline."""
    
    # Initialize MediaPipe pose detection
    mp_pose = mp.solutions.pose
    pose_detector = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    # Initialize timing logic processor with config parameters
    timing_processor = TimingLogicProcessor(
        high_threshold=config.get('threshold_high', 0.60),
        low_threshold=config.get('threshold_low', 0.35),
        hysteresis_margin=config.get('hysteresis_margin', 0.05),
        min_duration=config.get('min_duration', 0.08),
        smoothing_method=config.get('smoothing_method', 'ema'),
        smoothing_alpha=config.get('smoothing_alpha', 0.7),
        enable_tame_tsume=config.get('enable_tame_tsume', False)
    )
    
    # Open video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video file: {input_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Processing video: {frame_count} frames at {fps} FPS", file=sys.stderr)
    
    # Storage for frame analysis
    all_keypoints = []
    all_timestamps = []
    motion_intensity_scores = []
    
    frame_index = 0
    
    # Process each frame
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Calculate timestamp
        timestamp = frame_index / fps
        all_timestamps.append(timestamp)
        
        # Extract keypoints
        keypoints = extract_keypoints_from_frame(frame, pose_detector)
        all_keypoints.append(keypoints)
        
        # Calculate motion intensity if we have previous frames
        if frame_index > 0:
            # Get previous keypoints
            prev_keypoints = all_keypoints[frame_index - 1]
            
            # Calculate displacement
            displacement = calculate_displacement(keypoints, prev_keypoints)
            
            # Calculate velocity
            delta_t = 1.0 / fps
            velocity = calculate_velocity(displacement, delta_t)
            
            # Calculate acceleration (need at least 2 previous frames)
            acceleration = []
            if frame_index > 1:
                prev_prev_keypoints = all_keypoints[frame_index - 2]
                prev_displacement = calculate_displacement(prev_keypoints, prev_prev_keypoints)
                prev_velocity = calculate_velocity(prev_displacement, delta_t)
                acceleration = calculate_acceleration(velocity, prev_velocity, delta_t)
            
            # Calculate direction change (need at least 2 previous frames)
            direction_change = []
            if frame_index > 1:
                prev_prev_keypoints = all_keypoints[frame_index - 2]
                direction_change = calculate_direction_change(keypoints, prev_keypoints, prev_prev_keypoints)
            
            # Calculate pose change
            pose_change = calculate_pose_change(keypoints, prev_keypoints)
            
            # Calculate motion intensity score
            motion_intensity = calculate_motion_intensity_score(
                displacement, velocity, acceleration, direction_change, pose_change,
                weights=config.get('motion_weights')
            )
        else:
            # First frame has no motion
            motion_intensity = 0.0
        
        motion_intensity_scores.append(motion_intensity)
        
        frame_index += 1
        
        # Progress reporting
        if frame_index % 30 == 0:
            progress = (frame_index / frame_count) * 100
            print(f"Progress: {progress:.1f}% ({frame_index}/{frame_count})", file=sys.stderr)
    
    cap.release()
    pose_detector.close()
    
    print("Video analysis complete. Processing timing decisions...", file=sys.stderr)
    
    # Process timing decisions
    timing_decisions = timing_processor.process_sequence(
        motion_intensity_scores, 
        all_timestamps,
        accelerations=None  # Could be enhanced to pass acceleration data
    )
    
    # Create frame data
    frame_data = []
    for i, decision in enumerate(timing_decisions):
        frame_data.append(FrameData(
            frame_index=i,
            timestamp=all_timestamps[i],
            motion_intensity_score=motion_intensity_scores[i],
            motion_state=decision.motion_state.value,
            keypoints=all_keypoints[i] if config.get('save_keypoints', False) else None
        ))
    
    # Create analysis result
    analysis_result = AnalysisResult(
        source_video_path=input_path,
        output_video_path=output_path,
        analysis_timestamp=datetime.now().isoformat(),
        parameters=config,
        frame_data=frame_data
    )
    
    print("Analysis complete.", file=sys.stderr)
    return analysis_result


def main():
    parser = argparse.ArgumentParser(description='Process a video to identify key frames for animation.')
    parser.add_argument('--input', type=str, required=True, help='The absolute path to the source video file.')
    parser.add_argument('--output', type=str, required=True, help='The absolute path where the processed video will be saved.')
    parser.add_argument('--config', type=str, required=True, help='A JSON string containing analysis parameters.')

    try:
        args = parser.parse_args()
        
        # Parse config JSON
        try:
            config = json.loads(args.config)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config parameter: {e}")
        
        # Process the video
        analysis_result = process_video_pipeline(args.input, args.output, config)
        
        # Return success result
        result = {
            "status": "success",
            "output_video_path": args.output,
            "database_id": "pending",  # Will be set by T016 when TinyDB is integrated
            "message": "Video processed successfully."
        }
        print(json.dumps(result))
        sys.exit(0)
        
    except SystemExit as e:
        # This is to catch the exit from argparse, which is not an error in this context
        if e.code != 0:
            error_result = {
                "status": "error",
                "error_type": "ArgumentError",
                "message": f"Argument parsing failed."
            }
            print(json.dumps(error_result), file=sys.stderr)
            sys.exit(e.code)
    except Exception as e:
        error_result = {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
