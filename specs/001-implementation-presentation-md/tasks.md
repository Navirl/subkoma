# Tasks: Automated 2D Animation Frame Timing

**Input**: Design documents from `/specs/001-implementation-presentation-md/`

This document provides a detailed, dependency-ordered list of tasks to implement the feature.

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Paths are relative to the repository root.

---

## Phase 1: Project Setup & Environment

- [x] **T001**: Initialize a new Wails project with the Svelte template in the repository root. This will create the `frontend/` directory and main Go files.
- [x] **T002**: Create the `backend/` directory for the Python script and create an empty `backend/process_video.py` file.
- [x] **T003**: Create the `backend/requirements.txt` file and add `opencv-python`, `tinydb`, and `mediapipe` to it.
- [x] **T004**: [P] In the `frontend/` directory, create basic UI components in Svelte for video file input, a placeholder for parameter controls, and a "Run Analysis" button.

## Phase 2: Backend Core & TDD

**CRITICAL: Tests must be written and fail before their corresponding implementation.**

- [x] **T005**: [P] In `backend/`, create `tests/test_cli.py`. Write a test that uses `subprocess` to run `process_video.py` with mock arguments and asserts that it exits gracefully. This test MUST FAIL.
- [x] **T006**: [P] In `backend/`, create `tests/test_data_models.py`. Write tests to verify the creation of data structures representing the `AnalysisResult` and `FrameData` models from `data-model.md`.
- [ ] **T007**: In `backend/process_video.py`, implement the command-line argument parsing using `argparse` to satisfy the contract in `contracts/python_interface.md`. This should make test `T005` pass.
- [ ] **T008**: In `backend/`, create `data_models.py` to define the Python classes or dataclasses for `AnalysisResult` and `FrameData`. This should make test `T006` pass.
- [ ] **T009**: In `backend/`, create `tests/test_calculations.py`. Write failing tests for the feature calculation functions (e.g., displacement, velocity).
- [ ] **T010**: In `backend/`, create `calculations.py` and implement the feature calculation functions to make test `T009` pass.
- [ ] **T011**: In `backend/`, create `tests/test_timing_logic.py`. Write failing tests for the hysteresis and frame timing logic.
- [ ] **T012**: In `backend/`, create `timing_logic.py` and implement the hysteresis and frame selection logic to make test `T011` pass.

## Phase 3: Integration & Implementation

- [ ] **T013**: In `main.go`, implement the Go function that will be called from the Svelte UI. This function should accept the video path and parameters.
- [ ] **T014**: In the Go function from `T013`, implement the call to execute the `backend/process_video.py` script synchronously using `os/exec`. It must pass the arguments correctly and wait for the result.
- [ ] **T015**: In `backend/process_video.py`, integrate the full pipeline: 
    1. Read video frames using OpenCV.
    2. For each frame, run MediaPipe keypoint detection.
    3. Use the functions from `calculations.py` to get the `MotionIntensity` score.
    4. Use the functions from `timing_logic.py` to get the final `MotionState`.
- [ ] **T016**: In `backend/process_video.py`, implement the TinyDB integration. Initialize the database and save the final `AnalysisResult` document upon successful processing.
- [ ] **T017**: In `backend/process_video.py`, implement the final video generation loop using OpenCV's `VideoWriter`, applying the frame timing decisions from the `MotionState` of each frame.
- [ ] **T018**: In `backend/process_video.py`, ensure the final success or error JSON is printed to `stdout` or `stderr` as defined in the contract.

## Phase 4: UI Polish & Finalization

- [ ] **T019**: [P] In the Svelte frontend, implement the real parameter controls (e.g., sliders for thresholds) and bind them to the data sent to the Go backend.
- [ ] **T020**: [P] In the Svelte frontend, implement a modal loading overlay that is triggered by the "Run Analysis" button and closed when a result (success or error) is received from the Go backend.
- [ ] **T021**: In the Svelte frontend, implement the results display area, showing the path to the output video and key analysis data.
- [ ] **T022**: In `main.go` and the Svelte frontend, add robust error handling to display error messages received from the Python script.

## Parallel Execution Example

The following setup and initial test creation tasks can be performed concurrently:

```
# These tasks do not depend on each other and can be started in parallel.
Task: "T004: [P] In the frontend/ directory, create basic UI components..."
Task: "T005: [P] In backend/, create tests/test_cli.py..."
Task: "T006: [P] In backend/, create tests/test_data_models.py..."
```