# Implementation Plan: Automated 2D Animation Frame Timing

**Branch**: `001-implementation-presentation-md` | **Date**: 2025-09-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-implementation-presentation-md/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
The goal is to build a desktop application that automatically analyzes motion in 2D animation clips to apply appropriate frame timing (2-frame, 3-frame, or holds), saving animators manual effort. The technical approach is a hybrid Wails application using Svelte for the frontend, with a Go backend that orchestrates a Python script for the core video processing.

## Technical Context
**Language/Version**: Go 1.20+, Python 3.8+
**Primary Dependencies**: Wails, Svelte, OpenCV, MediaPipe, tinydb
**Storage**: TinyDB (file-based)
**Testing**: To be determined (likely `go test` for backend and a JS framework like Vitest for frontend)
**Target Platform**: Cross-platform desktop (Windows, macOS, Linux)
**Project Type**: Web application (Wails uses a web frontend)
**Performance Goals**: Process video files in a reasonable time without freezing the UI. Synchronous processing with a loading screen is the initial approach.
**Constraints**: The core analysis libraries (OpenCV, MediaPipe) are Python-based, constraining the backend implementation.
**Scale/Scope**: A desktop tool for individual animators.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The current plan adheres to the spirit of the constitution by separating concerns (Go for orchestration, Python for processing) and aiming for a simple, effective initial architecture. Formal testing procedures (TDD) will be defined in the `tasks.md` phase.

## Project Structure

### Documentation (this feature)
```
specs/001-implementation-presentation-md/
├── plan.md              # This file (/plan command output)
├── spec.md              # The feature specification
├── architecture.md      # The architecture decision record
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   └── python_interface.md
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application (when "frontend" + "backend" detected)
backend/          # This will be the Python script and its logic
├── process_video.py
└── ...

frontend/         # The Svelte project for the Wails UI
├── src/
│   ├── components/
│   └── ...
└── wails.json

main.go           # The main Go application entrypoint for Wails
go.mod
```

**Structure Decision**: Option 2: Web application. The Go and Svelte code will be managed by Wails at the root, while the Python backend logic will be organized in its own `backend/` directory.

## Phase 0: Outline & Research
The technical approach was determined through analysis of the feature requirements against available technologies. The final decision is a hybrid architecture.

**Output**:
- [research.md](./research.md)
- [architecture.md](./architecture.md)

## Phase 1: Design & Contracts
The data models and interface contracts have been defined based on the specification and the chosen architecture. A quickstart guide has been prepared for developers.

**Output**:
- [data-model.md](./data-model.md)
- [contracts/python_interface.md](./contracts/python_interface.md)
- [quickstart.md](./quickstart.md)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
The `/tasks` command will load `/templates/tasks-template.md` and the design artifacts from Phase 1 to generate a detailed `tasks.md` file. It will create tasks for each component of the architecture:
1.  **Wails/Go Backend**: Tasks for setting up the main application, calling the Python script, and managing the UI state (e.g., loading screen).
2.  **Python Backend**: Tasks for implementing the core logic: video I/O, keypoint detection, calculations, and database interaction.
3.  **Svelte Frontend**: Tasks for building the UI components, including the file input, parameter controls, and results display.

**Ordering Strategy**:
Tasks will be ordered to prioritize a vertical slice of functionality:
1.  Setup basic project structures (Wails, Python).
2.  Implement the bridge between Go and Python.
3.  Implement the core Python logic.
4.  Build the UI to interact with the backend.

**Estimated Output**: A detailed `tasks.md` file with 15-20 ordered tasks.

## Complexity Tracking
No constitutional violations requiring justification have been identified. The chosen architecture is deemed the simplest path to achieving the required functionality.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented
