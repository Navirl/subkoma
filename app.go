package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
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
	// Validate input parameters
	if request.InputPath == "" {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ValidationError",
			Message:   "Input path is required",
		}
	}
	
	if request.OutputPath == "" {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ValidationError",
			Message:   "Output path is required",
		}
	}
	
	if request.Config == "" {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ValidationError",
			Message:   "Config is required",
		}
	}
	
	// Get the current working directory to construct the path to the Python script
	workingDir, err := os.Getwd()
	if err != nil {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "SystemError",
			Message:   fmt.Sprintf("Failed to get working directory: %v", err),
		}
	}
	
	// Construct the path to the Python script
	scriptPath := filepath.Join(workingDir, "backend", "process_video.py")
	
	// Check if the Python script exists
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "FileNotFoundError",
			Message:   fmt.Sprintf("Python script not found at: %s", scriptPath),
		}
	}
	
	// Prepare the command arguments according to the contract
	args := []string{
		scriptPath,
		"--input", request.InputPath,
		"--output", request.OutputPath,
		"--config", request.Config,
	}
	
	// Execute the Python script synchronously
	cmd := exec.Command("python", args...)
	cmd.Dir = workingDir
	
	// Capture both stdout and stderr
	stdout, err := cmd.Output()
	if err != nil {
		// If there's an execution error, try to get stderr
		if exitError, ok := err.(*exec.ExitError); ok {
			stderr := string(exitError.Stderr)
			
			// Try to parse stderr as JSON error response
			var errorResponse ProcessVideoResponse
			if jsonErr := json.Unmarshal([]byte(stderr), &errorResponse); jsonErr == nil {
				return errorResponse
			}
			
			// If stderr is not valid JSON, return a generic error
			return ProcessVideoResponse{
				Status:    "error",
				ErrorType: "PythonExecutionError",
				Message:   fmt.Sprintf("Python script failed: %s", stderr),
			}
		}
		
		// Other execution errors
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ExecutionError",
			Message:   fmt.Sprintf("Failed to execute Python script: %v", err),
		}
	}
	
	// Parse the successful response from stdout
	var response ProcessVideoResponse
	if err := json.Unmarshal(stdout, &response); err != nil {
		return ProcessVideoResponse{
			Status:    "error",
			ErrorType: "ParseError",
			Message:   fmt.Sprintf("Failed to parse Python script response: %v", err),
		}
	}
	
	return response
}
