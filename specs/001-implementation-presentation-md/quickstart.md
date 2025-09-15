# Quickstart Guide

This guide provides instructions for setting up the development environment and running the application.

## Prerequisites

Ensure the following software is installed on your system.

1.  **Go**: Version 1.20 or later.
2.  **Wails**: Version 2. Follow the [official installation guide](https://wails.io/docs/gettingstarted/installation).
3.  **Node.js (NPM)**: Required by Wails for frontend dependency management.
4.  **Python**: Version 3.8 or later.
5.  **TinyDB**: No setup required, it will be installed as a Python dependency.

## 1. Clone the Repository

```bash
# Clone the project to your local machine
git clone <repository_url>
cd <project_directory>
```

## 2. Install Frontend Dependencies

Navigate to the `frontend/` directory and install the required NPM packages.

```bash
cd frontend
npm install
cd ..
```

## 3. Install Backend Dependencies (Python)

Create a virtual environment and install the required Python packages from `requirements.txt`.

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

*Note: The `requirements.txt` file will need to be created and should include `opencv-python`, `tinydb`, and a keypoint detection library like `mediapipe`.*

## 4. Configure Environment Variables

(No environment variables are required for TinyDB as the database path will be managed in the application code.)

## 5. Run the Application

Use the Wails CLI to run the application in development mode. This will build the application and open it, with hot-reloading enabled for both the Go backend and the Svelte frontend.

```bash
wails dev
```

## 6. Build the Application

To create a production-ready, single-executable binary, use the Wails build command.

```bash
wails build
```

This will generate an executable file in the `build/bin/` directory.