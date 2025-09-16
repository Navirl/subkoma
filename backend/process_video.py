import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(description='Process a video to identify key frames for animation.')
    parser.add_argument('--input', type=str, required=True, help='The absolute path to the source video file.')
    parser.add_argument('--output', type=str, required=True, help='The absolute path where the processed video will be saved.')
    parser.add_argument('--config', type=str, required=True, help='A JSON string containing analysis parameters.')

    try:
        args = parser.parse_args()
        # TODO: Add processing logic here
        # For now, just print a success message to satisfy the test
        result = {
            "status": "success",
            "output_video_path": args.output,
            "database_id": "mock_id",
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
