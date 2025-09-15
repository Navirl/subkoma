
import dataclasses
from typing import List, Optional

@dataclasses.dataclass
class Keypoint:
    x: int
    y: int
    name: Optional[str] = None

@dataclasses.dataclass
class FrameData:
    frame_index: int
    timestamp: float
    motion_intensity_score: float
    motion_state: str
    keypoints: Optional[List[Keypoint]] = None

@dataclasses.dataclass
class AnalysisResult:
    _id: int
    source_video_path: str
    output_video_path: str
    analysis_timestamp: str
    parameters: dict
    frame_data: List[FrameData]

def test_create_keypoint():
    keypoint = Keypoint(x=345, y=112, name="nose")
    assert keypoint.x == 345
    assert keypoint.y == 112
    assert keypoint.name == "nose"

def test_create_frame_data():
    keypoint = Keypoint(x=345, y=112, name="nose")
    frame_data = FrameData(
        frame_index=150,
        timestamp=6.25,
        motion_intensity_score=0.78,
        motion_state="HIGH",
        keypoints=[keypoint]
    )
    assert frame_data.frame_index == 150
    assert frame_data.timestamp == 6.25
    assert frame_data.motion_intensity_score == 0.78
    assert frame_data.motion_state == "HIGH"
    assert frame_data.keypoints[0].x == 345

def test_create_analysis_result():
    keypoint = Keypoint(x=345, y=112, name="nose")
    frame_data = FrameData(
        frame_index=150,
        timestamp=6.25,
        motion_intensity_score=0.78,
        motion_state="HIGH",
        keypoints=[keypoint]
    )
    analysis_result = AnalysisResult(
        _id=1,
        source_video_path="C:/Users/animator/clips/scene01.mp4",
        output_video_path="C:/Users/animator/clips/processed/scene01_timed.mp4",
        analysis_timestamp="2025-09-15T14:30:00Z",
        parameters={ "threshold_high": 0.6 },
        frame_data=[frame_data]
    )
    assert analysis_result._id == 1
    assert analysis_result.source_video_path == "C:/Users/animator/clips/scene01.mp4"
    assert analysis_result.output_video_path == "C:/Users/animator/clips/processed/scene01_timed.mp4"
    assert analysis_result.analysis_timestamp == "2025-09-15T14:30:00Z"
    assert analysis_result.parameters["threshold_high"] == 0.6
    assert len(analysis_result.frame_data) == 1
    assert analysis_result.frame_data[0].frame_index == 150
