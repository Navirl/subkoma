
import subprocess
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
import cv2
import numpy as np

def test_cli_runs_gracefully():
    """
    Tests that the process_video.py script runs with mock arguments and exits gracefully.
    """
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    script_path = os.path.join(project_root, 'backend', 'process_video.py')

    command = [
        sys.executable,
        script_path,
        '--input', 'mock/video.mp4',
        '--output', 'mock/output.mp4',
        '--config', '{}'  # Empty JSON object for now
    ]
    
    result = subprocess.run(command, capture_output=True, text=True, cwd=project_root)
    
    # The script should fail gracefully with a proper error message for non-existent file
    assert result.returncode == 1, f"Script should fail with exit code 1 for non-existent file"
    
    # Check that it outputs proper JSON error format
    stderr_lines = result.stderr.strip().split('\n')
    json_line = stderr_lines[-1]  # Last line should be JSON
    try:
        error_data = json.loads(json_line)
        assert error_data["status"] == "error"
        assert error_data["error_type"] == "FileNotFoundError"
        assert "Could not open video file" in error_data["message"]
    except json.JSONDecodeError:
        assert False, f"Expected JSON error output, got: {json_line}"


def test_generate_output_video_function():
    """
    Test that the generate_output_video function can be imported and called correctly.
    """
    # Import the function
    try:
        from backend.process_video import generate_output_video
        from backend.timing_logic import FrameTimingDecision, MotionState
    except ImportError:
        from process_video import generate_output_video
        from timing_logic import FrameTimingDecision, MotionState
    
    # Create mock timing decisions
    timing_decisions = [
        FrameTimingDecision(frame_index=0, motion_state=MotionState.LOW, should_keep=True, timing_multiplier=1),
        FrameTimingDecision(frame_index=1, motion_state=MotionState.MID, should_keep=True, timing_multiplier=3),
        FrameTimingDecision(frame_index=2, motion_state=MotionState.HIGH, should_keep=True, timing_multiplier=2),
    ]
    
    # Mock OpenCV functions
    with patch('cv2.VideoCapture') as mock_cap, \
         patch('cv2.VideoWriter') as mock_writer:
        
        # Setup mock video capture
        mock_cap_instance = MagicMock()
        mock_cap.return_value = mock_cap_instance
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480
        }.get(prop, 0)
        
        # Mock frame reading
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap_instance.read.side_effect = [
            (True, mock_frame),  # Frame 0
            (True, mock_frame),  # Frame 1  
            (True, mock_frame),  # Frame 2
            (False, None)        # End of video
        ]
        
        # Setup mock video writer
        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance
        mock_writer_instance.isOpened.return_value = True
        
        # Test the function
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            temp_path = temp_output.name
        
        try:
            generate_output_video('mock_input.mp4', temp_path, timing_decisions, 30.0)
            
            # Verify VideoCapture was called correctly
            mock_cap.assert_called_once_with('mock_input.mp4')
            
            # Verify VideoWriter was called correctly
            mock_writer.assert_called_once()
            
            # Verify frames were written according to timing decisions
            # Frame 0: 1 time, Frame 1: 3 times, Frame 2: 2 times = 6 total writes
            assert mock_writer_instance.write.call_count == 6
            
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except PermissionError:
                # On Windows, sometimes the file is still locked, just ignore
                pass


