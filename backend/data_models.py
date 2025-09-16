from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Keypoint:
    x: int
    y: int
    name: Optional[str] = None

@dataclass
class FrameData:
    frame_index: int
    timestamp: float
    motion_intensity_score: float
    motion_state: str
    keypoints: Optional[List[Keypoint]] = None

@dataclass
class AnalysisResult:
    source_video_path: str
    output_video_path: str
    analysis_timestamp: str
    parameters: Dict[str, Any]
    frame_data: List[FrameData]
    _id: Optional[int] = None # Managed by TinyDB, so it's optional on creation
