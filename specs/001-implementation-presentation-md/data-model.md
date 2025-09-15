# Data Model

This document defines the key data entities for the system, as identified in the feature specification. These models will be used for database persistence in TinyDB and for internal data structures.

## 1. AnalysisResult

This is the top-level document stored in the TinyDB database file, representing the complete analysis of a single video.

| Field Name | Data Type | Description | Required | Example |
| --- | --- | --- | --- | --- |
| `_id` | Integer | Unique identifier for the document, managed by TinyDB. | Yes | `1` |
| `source_video_path` | String | Absolute path to the original video file that was analyzed. | Yes | `"C:/Users/animator/clips/scene01.mp4"` |
| `output_video_path` | String | Absolute path to the generated video file with adjusted timing. | Yes | `"C:/Users/animator/clips/processed/scene01_timed.mp4"` |
| `analysis_timestamp` | ISODate | The date and time when the analysis was performed. | Yes | `2025-09-15T14:30:00Z` |
| `parameters` | Object | The settings used for this analysis. | Yes | `{ "threshold_high": 0.6, ... }` |
| `frame_data` | Array of [FrameData](#2-framedata) | An array containing the detailed analysis for each frame. | Yes | `[ { "frame_index": 0, ... }, ... ]` |

---

## 2. FrameData

This is a sub-document embedded within the `AnalysisResult`'s `frame_data` array. It holds all calculated information for a single frame.

| Field Name | Data Type | Description | Required | Example |
| --- | --- | --- | --- | --- |
| `frame_index` | Integer | The 0-based index of the frame in the original video. | Yes | `150` |
| `timestamp` | Float | The timestamp of the frame in seconds. | Yes | `6.25` |
| `motion_intensity_score` | Float | The calculated `MotionIntensity` score, ranging from 0.0 to 1.0. | Yes | `0.78` |
| `motion_state` | String | The final classification label for the frame. | Yes | `"HIGH"` |
| `keypoints` | Array of [Keypoint](#3-keypoint) | The array of detected keypoints for this frame. Optional, for debug/visualization purposes. | No | `[ { "x": 345, "y": 112 }, ... ]` |

---

## 3. Keypoint

Represents a single 2D coordinate detected on a frame.

| Field Name | Data Type | Description | Required | Example |
| --- | --- | --- | --- | --- |
| `x` | Integer | The x-coordinate of the keypoint in pixels. | Yes | `345` |
| `y` | Integer | The y-coordinate of the keypoint in pixels. | Yes | `112` |
| `name` | String | Optional name or index of the keypoint (e.g., "nose", "left_wrist"). | No | `"nose"` |