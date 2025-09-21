package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// App struct
type App struct {
	ctx context.Context
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

// Greet returns a greeting for the given name
func (a *App) Greet(name string) string {
	return fmt.Sprintf("Hello %s, It's show time!", name)
}

// ProcessVideoRequest represents the parameters for video processing
type ProcessVideoRequest struct {
	InputPath  string `json:"input_path"`
	OutputPath string `json:"output_path"`
	Config     string `json:"config"` // JSON string containing analysis parameters
}

// ProcessVideoResponse represents the response from video processing
type ProcessVideoResponse struct {
	Status           string `json:"status"`
	OutputVideoPath  string `json:"output_video_path,omitempty"`
	DatabaseID       string `json:"database_id,omitempty"`
	Message          string `json:"message"`
	ErrorType        string `json:"error_type,omitempty"`
}

// ProcessVideo processes a video file using the Python backend
// This function will be called from the Svelte UI
func (a *App) ProcessVideo(request ProcessVideoRequest) ProcessVideoResponse {
	// Enhanced input validation
	if request.InputPath == "" {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ValidationError",
			Message:   "Input video path is required. Please select a video file.",
		}
	}
	
	if request.OutputPath == "" {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ValidationError",
			Message:   "Output path is required. Please specify where to save the processed video.",
		}
	}
	
	if request.Config == "" {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ValidationError",
			Message:   "Analysis configuration is required. Please check your parameter settings.",
		}
	}
	
	// Validate input file exists and is accessible
	if _, err := os.Stat(request.InputPath); os.IsNotExist(err) {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "FileNotFoundError",
			Message:   fmt.Sprintf("Input video file not found: %s. Please check the file path and try again.", request.InputPath),
		}
	} else if err != nil {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "FileAccessError",
			Message:   fmt.Sprintf("Cannot access input video file: %s. Error: %v", request.InputPath, err),
		}
	}
	
	// Validate config is valid JSON
	var configTest interface{}
	if err := json.Unmarshal([]byte(request.Config), &configTest); err != nil {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ConfigurationError",
			Message:   fmt.Sprintf("Invalid configuration format: %v. Please reset parameters and try again.", err),
		}
	}
	
	// Get the current working directory to construct the path to the Python script
	workingDir, err := os.Getwd()
	if err != nil {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "SystemError",
			Message:   fmt.Sprintf("System error: Failed to get working directory: %v", err),
		}
	}
	
	// Construct the path to the Python script
	scriptPath := filepath.Join(workingDir, "backend", "process_video.py")
	
	// Check if the Python script exists
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "InstallationError",
			Message:   fmt.Sprintf("Backend processing script not found at: %s. Please check your installation.", scriptPath),
		}
	}
	
	// Check if output directory exists and is writable
	outputDir := filepath.Dir(request.OutputPath)
	if outputDir != "" {
		if _, err := os.Stat(outputDir); os.IsNotExist(err) {
			// Try to create the directory
			if err := os.MkdirAll(outputDir, 0755); err != nil {
				return ProcessVideoResponse{
					Status:    "error",
					ErrorType: "FileSystemError",
					Message:   fmt.Sprintf("Cannot create output directory: %s. Error: %v", outputDir, err),
				}
			}
		}
	}
	
	// Prepare the command arguments according to the contract
	args := []string{
		scriptPath,
		"--input", request.InputPath,
		"--output", request.OutputPath,
		"--config", request.Config,
	}
	
	// Add debug flags if environment variable is set
	if os.Getenv("PYTHON_DEBUG") == "true" {
		args = append(args, "--debug")
		// Optionally wait for debugger
		if os.Getenv("PYTHON_DEBUG_WAIT") == "true" {
			args = append(args, "--debug-wait")
		}
		// Custom debug port
		if port := os.Getenv("PYTHON_DEBUG_PORT"); port != "" {
			args = append(args, "--debug-port", port)
		}
	}
	
	// Execute the Python script using uv run for proper virtual environment handling
	uvArgs := append([]string{"run", "python"}, args...)
	cmd := exec.Command("uv", uvArgs...)
	cmd.Dir = workingDir
	
	// Capture both stdout and stderr
	stdout, err := cmd.Output()
	var stderr []byte
	
	// Handle execution errors
	cmdErr := err
	
	// Handle execution errors with detailed messages
	if cmdErr != nil {
		// Extract stderr from the error if it's an ExitError
		if exitError, ok := cmdErr.(*exec.ExitError); ok {
			stderr = exitError.Stderr
		}
		
		stderrStr := string(stderr)
		
		// Try to parse stderr as JSON error response first
		var errorResponse ProcessVideoResponse
		if len(stderr) > 0 && json.Unmarshal(stderr, &errorResponse) == nil {
			// Enhance the error message with more context
			if errorResponse.Message != "" {
				errorResponse.Message = fmt.Sprintf("Processing failed: %s", errorResponse.Message)
			}
			return errorResponse
		}
		
		// Handle specific error types based on stderr content
		if len(stderrStr) > 0 {
			// Check for common error patterns
			if contains(stderrStr, "FileNotFoundError") || contains(stderrStr, "No such file") {
				return ProcessVideoResponse{
					Status:    "error",
					ErrorType: "FileNotFoundError",
					Message:   fmt.Sprintf("File not found during processing. Details: %s", stderrStr),
				}
			} else if contains(stderrStr, "PermissionError") || contains(stderrStr, "Permission denied") {
				return ProcessVideoResponse{
					Status:    "error",
					ErrorType: "PermissionError",
					Message:   fmt.Sprintf("Permission denied. Please check file permissions. Details: %s", stderrStr),
				}
			} else if contains(stderrStr, "ModuleNotFoundError") || contains(stderrStr, "ImportError") {
				return ProcessVideoResponse{
					Status:    "error",
					ErrorType: "DependencyError",
					Message:   fmt.Sprintf("Missing required Python dependencies. Please install requirements. Details: %s", stderrStr),
				}
			} else if contains(stderrStr, "OutOfMemoryError") || contains(stderrStr, "MemoryError") {
				return ProcessVideoResponse{
					Status:    "error",
					ErrorType: "MemoryError",
					Message:   "Insufficient memory to process the video. Try with a smaller video file or close other applications.",
				}
			} else if contains(stderrStr, "cv2.error") || contains(stderrStr, "OpenCV") {
				return ProcessVideoResponse{
					Status:    "error",
					ErrorType: "VideoProcessingError",
					Message:   fmt.Sprintf("Video processing error. The video file may be corrupted or in an unsupported format. Details: %s", stderrStr),
				}
			}
			
			// Generic error with stderr content
			return ProcessVideoResponse{
				Status:    "error",
				ErrorType: "PythonExecutionError",
				Message:   fmt.Sprintf("Processing failed with error: %s", stderrStr),
			}
		}
		
		// Error without stderr content
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ExecutionError",
			Message:   fmt.Sprintf("Python script execution failed: %v", cmdErr),
		}
	}
	
	// Handle successful execution
	if len(stdout) == 0 {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "OutputError",
			Message:   "No output received from processing script. The process may have failed silently.",
		}
	}
	
	// Parse the successful response from stdout
	var response ProcessVideoResponse
	if err := json.Unmarshal(stdout, &response); err != nil {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ParseError",
			Message:   fmt.Sprintf("Failed to parse processing results: %v. Raw output: %s", err, string(stdout)),
		}
	}
	
	// Validate the response has required fields
	if response.Status == "" {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ResponseError",
			Message:   "Invalid response format from processing script.",
		}
	}
	
	// Enhance success message
	if response.Status == "success" && response.Message == "" {
		response.Message = "Video processing completed successfully."
	}
	
	return response
}

// SelectVideoFile opens a file dialog to select a video file
func (a *App) SelectVideoFile() (string, error) {
	options := runtime.OpenDialogOptions{
		Title: "Select Video File",
		Filters: []runtime.FileFilter{
			{
				DisplayName: "Video Files",
				Pattern:     "*.mp4;*.avi;*.mov;*.mkv;*.wmv;*.flv;*.webm",
			},
			{
				DisplayName: "All Files",
				Pattern:     "*",
			},
		},
	}

	filePath, err := runtime.OpenFileDialog(a.ctx, options)
	if err != nil {
		return "", fmt.Errorf("failed to open file dialog: %v", err)
	}

	return filePath, nil
}

// Helper function to check if a string contains a substring (case-insensitive)
func contains(s, substr string) bool {
	return strings.Contains(strings.ToLower(s), strings.ToLower(substr))
}
