
import subprocess
import sys

def test_cli_runs_gracefully():
    """
    Tests that the process_video.py script runs with mock arguments and exits gracefully.
    """
    command = [
        sys.executable,
        '../process_video.py',
        '--video_path', 'mock/video.mp4',
        '--output_path', 'mock/output.mp4',
        '--db_path', 'mock/db.json'
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    assert result.returncode == 0, f"Script failed with exit code {result.returncode}\nStderr: {result.stderr}"

