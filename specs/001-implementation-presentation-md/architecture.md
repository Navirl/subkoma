# Architecture Decision Record

This document outlines the chosen technical architecture for the Automated 2D Animation Frame Timing System.

## High-Level Architecture

The system will be a desktop application built using Wails. It will follow a hybrid architecture that leverages both Go and Python to combine a responsive user interface with powerful video processing capabilities.

- **Frontend (UI)**: The user interface will be built as a modern web application using **Svelte**.
- **Application Wrapper & Backend Orchestrator**: **Wails** will be used to wrap the Svelte frontend into a native desktop application. The Go backend provided by Wails will handle UI events and orchestrate the core processing.
- **Core Processing Backend**: All heavy-lifting (video analysis, calculation, and generation) will be handled by a single, dedicated **Python** script.
- **Database**: **TinyDB**, a lightweight document database, will be used to store the analysis results in a single JSON file.

## Interaction Model

The interaction between the Go orchestrator and the Python backend will be **synchronous**.

1.  The user initiates a task from the Svelte UI.
2.  The Wails Go backend receives the request.
3.  The Go backend triggers a loading screen or busy indicator in the UI.
4.  The Go backend executes the main Python script as a command-line process, passing the input video path and parameters as arguments.
5.  The Go backend waits for the Python process to complete.
6.  The Python script performs all analysis and generates the output video file and database records. It returns the path to the output file upon completion.
7.  The Go backend receives the result from the completed Python process.
8.  The Go backend hides the loading screen and pushes the results (e.g., the output file path) to the UI.

This synchronous model with a loading screen was chosen to reduce initial development complexity, prioritizing a functional deliverable over a more complex asynchronous UI.

## Core Libraries and Tools

- **Python Backend**:
  - **`OpenCV`**: Will be used for primary video I/O operations, including reading frames from the source video, extracting the framerate, and writing the final processed video file.
  - **`MediaPipe` / `OpenPose`**: A keypoint detection library will be integrated to analyze character motion from the video frames.
  - **`FFmpeg`**: While `OpenCV` will be the primary tool, `FFmpeg` may be used as a more efficient alternative for final video assembly if performance becomes a concern.
  - **`tinydb`**: A lightweight, pure Python document database for storing results.
- **Go Backend**:
  - Standard library `os/exec` will be used to execute the Python script.
- **Frontend**:
  - `Svelte`: For building the user interface components.
ponents.
