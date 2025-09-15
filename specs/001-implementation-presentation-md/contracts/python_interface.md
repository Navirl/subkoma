# Python Script Interface

This document defines the contract for executing the main Python processing script from the Go backend.

## Execution

The script will be executed as a command-line process.

```bash
python process_video.py [arguments]
```

## Command-Line Arguments

The script will accept the following arguments to control its execution.

| Argument | Example | Description | Required |
| --- | --- | --- | --- |
| `--input` | `"C:/path/to/video.mp4"` | The absolute path to the source video file to be processed. | Yes |
| `--output` | `"C:/path/to/output.mp4"` | The absolute path where the processed video file will be saved. | Yes |
| `--config` | `'{"threshold_high": 0.65, ...}'` | A JSON string containing the analysis parameters (thresholds, weights, etc.). | Yes |

## Output

### 1. Standard Output (`stdout`)

Upon successful completion, the script will print a single JSON string to standard output containing the results of the operation.

#### Success JSON Structure

```json
{
  "status": "success",
  "output_video_path": "C:/path/to/output.mp4",
  "database_id": "63d8b9e4e4b0f8b8a8b8a8b8",
  "message": "Video processed successfully."
}
```

### 2. Standard Error (`stderr`)

- **Progress**: During execution, the script may write progress information to standard error to be captured for logging. This is an optional enhancement and not part of the core contract.
- **Errors**: If a fatal error occurs during processing, the script will print an error message to standard error and exit with a non-zero status code. The Go backend should always capture `stderr`.

#### Error JSON Structure

It is recommended that errors also be structured as JSON for easier parsing.

```json
{
  "status": "error",
  "error_type": "FileNotFoundError",
  "message": "Input video not found at specified path."
}
```
