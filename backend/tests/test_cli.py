
import subprocess
import sys
import os

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
    
    assert result.returncode == 0, f"Script failed with exit code {result.returncode}\nStderr: {result.stderr}"


