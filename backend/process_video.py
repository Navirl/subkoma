import argparse
import json
import sys
import cv2
import mediapipe as mp
import numpy as np
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from tinydb import TinyDB

try:
    from backend.data_models import Keypoint, FrameData, AnalysisResult
    from backend.calculations import (
        calculate_displacement, calculate_velocity, calculate_acceleration,
        calculate_direction_change, calculate_pose_change, calculate_motion_intensity_score
    )
    from backend.timing_logic import TimingLogicProcessor, MotionState, FrameTimingDecision
except ImportError:
    # When running directly from backend directory
    from data_models import Keypoint, FrameData, AnalysisResult
    from calculations import (
        calculate_displacement, calculate_velocity, calculate_acceleration,
        calculate_direction_change, calculate_pose_change, calculate_motion_intensity_score
    )
    from timing_logic import TimingLogicProcessor, MotionState, FrameTimingDecision


def initialize_database(db_path: str = "analysis_results.json") -> TinyDB:
    """Initialize TinyDB database for storing analysis results."""
    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    return TinyDB(db_path)


def save_analysis_result(analysis_result: AnalysisResult, db_path: str = "analysis_results.json") -> int:
    """Save the AnalysisResult to TinyDB and return the document ID."""
    db = initialize_database(db_path)
    
    # Convert the dataclass to a dictionary for TinyDB storage
    # We need to handle nested dataclasses (FrameData and Keypoint)
    result_dict = {
        "source_video_path": analysis_result.source_video_path,
        "output_video_path": analysis_result.output_video_path,
        "analysis_timestamp": analysis_result.analysis_timestamp,
        "parameters": analysis_result.parameters,
        "frame_data": []
    }
    
    # Convert frame data to dictionaries
    for frame in analysis_result.frame_data:
        frame_dict = {
            "frame_index": frame.frame_index,
            "timestamp": frame.timestamp,
            "motion_intensity_score": frame.motion_intensity_score,
            "motion_state": frame.motion_state,
            "keypoints": None
        }
        
        # Convert keypoints if they exist
        if frame.keypoints:
            frame_dict["keypoints"] = [
                {
                    "x": kp.x,
                    "y": kp.y,
                    "name": kp.name
                }
                for kp in frame.keypoints
            ]
        
        result_dict["frame_data"].append(frame_dict)
    
    # Insert the document and get the ID
    doc_id = db.insert(result_dict)
    
    # Update the analysis_result object with the database ID
    analysis_result._id = doc_id
    
    db.close()
    return doc_id


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
    
    try:
        # Initialize MediaPipe pose detection
        mp_pose = mp.solutions.pose
        pose_detector = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    except Exception as e:
        raise ImportError(f"Failed to initialize MediaPipe pose detection: {e}")
    
    try:
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
    except Exception as e:
        raise ValueError(f"Failed to initialize timing processor with given configuration: {e}")
    
    # Open video with enhanced error handling
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video file: {input_path}. Please check if the file exists and is a valid video format.")
    
    # Get video properties and validate them
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if fps <= 0:
        cap.release()
        raise ValueError(f"Invalid video frame rate: {fps}. The video file may be corrupted.")
    
    if frame_count <= 0:
        cap.release()
        raise ValueError(f"Invalid video frame count: {frame_count}. The video file may be corrupted or empty.")
    
    if width <= 0 or height <= 0:
        cap.release()
        raise ValueError(f"Invalid video dimensions: {width}x{height}. The video file may be corrupted.")
    
    print(f"Processing video: {frame_count} frames at {fps} FPS ({width}x{height})", file=sys.stderr)
    
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
    
    print("Analysis complete. Generating output video...", file=sys.stderr)
    
    # Generate the output video with timing decisions applied
    generate_output_video(input_path, output_path, timing_decisions, fps)
    
    print("Output video generation complete.", file=sys.stderr)
    return analysis_result


def generate_output_video(input_path: str, output_path: str, timing_decisions: List[FrameTimingDecision], fps: float) -> None:
    """
    Generate the output video applying frame timing decisions.
    
    Args:
        input_path: Path to the input video file
        output_path: Path where the output video will be saved
        timing_decisions: List of FrameTimingDecision objects
        fps: Original video frame rate
    """
    # Open input video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open input video file: {input_path}")
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Define codec and create VideoWriter
    # Use mp4v codec for MP4 files, or XVID for AVI files
    if output_path.lower().endswith('.mp4'):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    elif output_path.lower().endswith('.avi'):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
    else:
        # Default to mp4v
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Create VideoWriter with original fps (timing is controlled by frame repetition)
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        cap.release()
        raise RuntimeError(f"Could not create output video file: {output_path}")
    
    print(f"Generating output video: {width}x{height} at {fps} FPS", file=sys.stderr)
    
    frame_index = 0
    total_output_frames = 0
    
    # Process each frame according to timing decisions
    while frame_index < len(timing_decisions):
        # Read the frame
        ret, frame = cap.read()
        if not ret:
            print(f"Warning: Could not read frame {frame_index}, stopping video generation", file=sys.stderr)
            break
        
        # Get timing decision for this frame
        decision = timing_decisions[frame_index]
        
        # Write the frame multiple times based on timing_multiplier
        for _ in range(decision.timing_multiplier):
            out.write(frame)
            total_output_frames += 1
        
        frame_index += 1
        
        # Progress reporting
        if frame_index % 30 == 0:
            progress = (frame_index / len(timing_decisions)) * 100
            print(f"Video generation progress: {progress:.1f}% ({frame_index}/{len(timing_decisions)})", file=sys.stderr)
    
    # Release everything
    cap.release()
    out.release()
    
    print(f"Output video generated: {total_output_frames} frames written", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='Process a video to identify key frames for animation.')
    parser.add_argument('--input', type=str, required=True, help='The absolute path to the source video file.')
    parser.add_argument('--output', type=str, required=True, help='The absolute path where the processed video will be saved.')
    parser.add_argument('--config', type=str, required=True, help='A JSON string containing analysis parameters.')

    try:
        args = parser.parse_args()
        
        # Enhanced input validation
        if not args.input:
            raise ValueError("Input path cannot be empty")
        
        if not args.output:
            raise ValueError("Output path cannot be empty")
            
        if not args.config:
            raise ValueError("Configuration cannot be empty")
        
        # Validate input file exists and is accessible
        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Input video file not found: {args.input}")
        
        if not os.access(args.input, os.R_OK):
            raise PermissionError(f"Cannot read input video file: {args.input}")
        
        # Validate output directory exists or can be created
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                raise PermissionError(f"Cannot create output directory {output_dir}: {e}")
        
        # Check if output directory is writable
        if output_dir and not os.access(output_dir, os.W_OK):
            raise PermissionError(f"Cannot write to output directory: {output_dir}")
        
        # Parse and validate config JSON
        try:
            config = json.loads(args.config)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config parameter: {e}")
        
        # Validate config structure
        required_keys = ['threshold_high', 'threshold_low', 'motion_weights']
        for key in required_keys:
            if key not in config:
                print(f"Warning: Missing config key '{key}', using default value", file=sys.stderr)
        
        # Validate motion weights if present
        if 'motion_weights' in config:
            weights = config['motion_weights']
            if not isinstance(weights, dict):
                raise ValueError("motion_weights must be a dictionary")
            
            expected_weight_keys = ['displacement', 'velocity', 'acceleration', 'direction_change', 'pose_change']
            for key in expected_weight_keys:
                if key not in weights:
                    print(f"Warning: Missing motion weight '{key}', using default value", file=sys.stderr)
                elif not isinstance(weights[key], (int, float)):
                    raise ValueError(f"Motion weight '{key}' must be a number")
        
        print(f"Starting video processing: {args.input}", file=sys.stderr)
        print(f"Output will be saved to: {args.output}", file=sys.stderr)
        
        # Process the video
        analysis_result = process_video_pipeline(args.input, args.output, config)
        
        # Verify output file was created
        if not os.path.exists(args.output):
            raise RuntimeError(f"Output video file was not created: {args.output}")
        
        # Save to database and get the ID
        print("Saving analysis results to database...", file=sys.stderr)
        try:
            database_id = save_analysis_result(analysis_result)
            print(f"Analysis saved with database ID: {database_id}", file=sys.stderr)
        except Exception as db_error:
            print(f"Warning: Failed to save to database: {db_error}", file=sys.stderr)
            database_id = None
        
        # Return success result
        result = {
            "status": "success",
            "output_video_path": args.output,
            "database_id": database_id,
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
                "message": "Invalid command line arguments. Please check your input parameters."
            }
            print(json.dumps(error_result), file=sys.stderr)
            sys.exit(e.code)
    except FileNotFoundError as e:
        error_result = {
            "status": "error",
            "error_type": "FileNotFoundError",
            "message": str(e)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        error_result = {
            "status": "error",
            "error_type": "PermissionError",
            "message": str(e)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        error_result = {
            "status": "error",
            "error_type": "ValidationError",
            "message": str(e)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        error_result = {
            "status": "error",
            "error_type": "DependencyError",
            "message": f"Missing required Python package: {e}. Please install dependencies with: pip install -r requirements.txt"
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
    except MemoryError as e:
        error_result = {
            "status": "error",
            "error_type": "MemoryError",
            "message": "Insufficient memory to process the video. Try with a smaller video file or close other applications."
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Enhanced error reporting for unexpected errors
        error_type = type(e).__name__
        error_message = str(e)
        
        # Add context for common error types
        if "cv2" in error_message.lower() or "opencv" in error_message.lower():
            error_type = "VideoProcessingError"
            error_message = f"Video processing failed: {error_message}. The video file may be corrupted or in an unsupported format."
        elif "mediapipe" in error_message.lower():
            error_type = "PoseDetectionError"
            error_message = f"Pose detection failed: {error_message}. This may be due to an unsupported video format or corrupted frames."
        elif "tinydb" in error_message.lower():
            error_type = "DatabaseError"
            error_message = f"Database operation failed: {error_message}. Check file permissions and disk space."
        
        error_result = {
            "status": "error",
            "error_type": error_type,
            "message": error_message
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
