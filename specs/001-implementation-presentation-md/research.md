# Research & Discovery

This document summarizes the research activities conducted during the planning phase.

## Summary

The primary research objective was to determine a suitable technical architecture for building a desktop application with a web-based UI that could also handle intensive video processing tasks.

Initial exploration and discussion centered on the following key areas:

1.  **Application Framework**: How to build a cross-platform desktop app using web technologies.
2.  **Backend Processing**: How to execute the core motion analysis algorithms, which are computationally expensive and rely on specific Python libraries.
3.  **Inter-process Communication**: If the UI and backend processing were in separate processes/languages, how they would communicate.

## Outcome

The research phase concluded with a clear architectural decision, which is documented in detail in the **Architecture Decision Record**.

- **[Architecture Decision Record](./architecture.md)**

Key findings that led to this decision include:

- **Wails** was identified as a modern, performant framework for creating desktop applications with Go and web technologies.
- The core video analysis libraries (**MediaPipe**, **OpenCV**) are mature and best-supported in the **Python** ecosystem. Go-native equivalents are not sufficiently mature for this project's needs.
- A hybrid model combining a Wails/Go frontend orchestrator with a Python backend script was initially considered but deemed overly complex for the initial version due to the overhead of inter-process communication.
- A simpler, synchronous model where the Wails/Go application calls a monolithic Python script and waits for its completion was chosen to reduce development overhead and risk.

No further research is required to proceed with the design and implementation phases.
