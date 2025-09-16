import numpy as np
import pytest
from backend.data_models import Keypoint
from backend.calculations import (
    calculate_displacement,
    calculate_velocity,
    calculate_acceleration,
    calculate_direction_change,
    calculate_pose_change,
    calculate_motion_intensity_score,
)

def test_calculate_displacement():
    """
    Tests the calculation of displacement between two sets of keypoints.
    """
    keypoints_t0 = [Keypoint(x=10, y=20), Keypoint(x=30, y=40)]
    keypoints_t1 = [Keypoint(x=13, y=24), Keypoint(x=35, y=45)]
    
    # Expected displacement:
    # Point 1: sqrt((13-10)^2 + (24-20)^2) = sqrt(9 + 16) = 5
    # Point 2: sqrt((35-30)^2 + (45-40)^2) = sqrt(25 + 25) = sqrt(50) ~= 7.071
    # Individual displacements: [5.0, 7.071]
    expected_displacements = [5.0, np.sqrt(50.0)]
    
    displacements = calculate_displacement(keypoints_t1, keypoints_t0)
    
    assert displacements is not None
    assert len(displacements) == 2
    assert np.allclose(displacements, expected_displacements)

def test_calculate_velocity():
    """
    Tests the calculation of velocity from displacements.
    """
    displacements = [5.0, 10.0]
    delta_t = 1/30.0  # Assuming 30 FPS

    # Expected velocity:
    # V1 = 5.0 / (1/30) = 150.0
    # V2 = 10.0 / (1/30) = 300.0
    expected_velocities = [150.0, 300.0]

    velocities = calculate_velocity(displacements, delta_t)

    assert velocities is not None
    assert len(velocities) == 2
    assert np.allclose(velocities, expected_velocities)

def test_calculate_displacement_no_keypoints():
    """
    Tests displacement calculation with empty keypoint lists.
    """
    displacements = calculate_displacement([], [])
    assert displacements == []

def test_calculate_velocity_no_displacements():
    """
    Tests velocity calculation with an empty displacement list.
    """
    velocities = calculate_velocity([], 1/30.0)
    assert velocities == []
def test_calculate_acceleration():
    """
    Tests the calculation of acceleration from velocities.
    """
    velocities_t0 = [100.0, 200.0]
    velocities_t1 = [150.0, 300.0]
    delta_t = 1/30.0  # Assuming 30 FPS

    # Expected acceleration:
    # A1 = (150.0 - 100.0) / (1/30) = 50.0 / (1/30) = 1500.0
    # A2 = (300.0 - 200.0) / (1/30) = 100.0 / (1/30) = 3000.0
    expected_accelerations = [1500.0, 3000.0]

    accelerations = calculate_acceleration(velocities_t1, velocities_t0, delta_t)

    assert accelerations is not None
    assert len(accelerations) == 2
    assert np.allclose(accelerations, expected_accelerations)

def test_calculate_direction_change():
    """
    Tests the calculation of direction change between consecutive frames.
    """
    keypoints_t0 = [Keypoint(x=10, y=20), Keypoint(x=30, y=40)]
    keypoints_t1 = [Keypoint(x=15, y=20), Keypoint(x=30, y=45)]  # Moving right and up
    keypoints_t2 = [Keypoint(x=15, y=15), Keypoint(x=25, y=45)]  # Moving down and left

    # Expected direction changes should be calculated based on angle differences
    direction_changes = calculate_direction_change(keypoints_t2, keypoints_t1, keypoints_t0)

    assert direction_changes is not None
    assert len(direction_changes) == 2
    assert all(0 <= change <= np.pi for change in direction_changes)  # Direction change should be between 0 and π

def test_calculate_pose_change():
    """
    Tests the calculation of pose change between two sets of keypoints.
    """
    keypoints_t0 = [
        Keypoint(x=100, y=100),  # head
        Keypoint(x=90, y=120),   # left shoulder
        Keypoint(x=110, y=120),  # right shoulder
        Keypoint(x=85, y=140),   # left elbow
        Keypoint(x=115, y=140),  # right elbow
    ]
    keypoints_t1 = [
        Keypoint(x=100, y=100),  # head (same)
        Keypoint(x=85, y=125),   # left shoulder (moved)
        Keypoint(x=115, y=125),  # right shoulder (moved)
        Keypoint(x=80, y=145),   # left elbow (moved)
        Keypoint(x=120, y=145),  # right elbow (moved)
    ]

    pose_change = calculate_pose_change(keypoints_t1, keypoints_t0)

    assert pose_change is not None
    assert isinstance(pose_change, float)
    assert pose_change >= 0.0  # Pose change should be non-negative

def test_calculate_motion_intensity_score():
    """
    Tests the calculation of the overall motion intensity score.
    """
    # Mock data for different motion components
    displacement = [5.0, 7.0, 3.0]
    velocity = [150.0, 210.0, 90.0]
    acceleration = [1500.0, 2100.0, 900.0]
    direction_change = [0.5, 0.8, 0.2]
    pose_change = 0.6

    # Test with default weights
    intensity_score = calculate_motion_intensity_score(
        displacement, velocity, acceleration, direction_change, pose_change
    )

    assert intensity_score is not None
    assert isinstance(intensity_score, float)
    assert 0.0 <= intensity_score <= 1.0  # Score should be normalized between 0 and 1

def test_calculate_motion_intensity_score_with_weights():
    """
    Tests the calculation of motion intensity score with custom weights.
    """
    displacement = [5.0, 7.0, 3.0]
    velocity = [150.0, 210.0, 90.0]
    acceleration = [1500.0, 2100.0, 900.0]
    direction_change = [0.5, 0.8, 0.2]
    pose_change = 0.6

    # Custom weights that sum to 1.0
    weights = {
        'displacement': 0.3,
        'velocity': 0.3,
        'acceleration': 0.2,
        'direction_change': 0.1,
        'pose_change': 0.1
    }

    intensity_score = calculate_motion_intensity_score(
        displacement, velocity, acceleration, direction_change, pose_change, weights
    )

    assert intensity_score is not None
    assert isinstance(intensity_score, float)
    assert 0.0 <= intensity_score <= 1.0

def test_calculate_acceleration_no_velocities():
    """
    Tests acceleration calculation with empty velocity lists.
    """
    accelerations = calculate_acceleration([], [], 1/30.0)
    assert accelerations == []

def test_calculate_direction_change_no_keypoints():
    """
    Tests direction change calculation with empty keypoint lists.
    """
    direction_changes = calculate_direction_change([], [], [])
    assert direction_changes == []

def test_calculate_pose_change_no_keypoints():
    """
    Tests pose change calculation with empty keypoint lists.
    """
    pose_change = calculate_pose_change([], [])
    assert pose_change == 0.0

def test_calculate_motion_intensity_score_empty_data():
    """
    Tests motion intensity score calculation with empty data.
    """
    intensity_score = calculate_motion_intensity_score([], [], [], [], 0.0)
    assert intensity_score == 0.0