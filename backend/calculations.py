import numpy as np
from typing import List, Dict, Optional
from backend.data_models import Keypoint


def calculate_displacement(keypoints_current: List[Keypoint], keypoints_previous: List[Keypoint]) -> List[float]:
    """
    Calculate displacement between two sets of keypoints.
    
    Args:
        keypoints_current: Current frame keypoints
        keypoints_previous: Previous frame keypoints
        
    Returns:
        List of displacement values for each keypoint pair
    """
    if not keypoints_current or not keypoints_previous:
        return []
    
    if len(keypoints_current) != len(keypoints_previous):
        return []
    
    displacements = []
    for curr, prev in zip(keypoints_current, keypoints_previous):
        dx = curr.x - prev.x
        dy = curr.y - prev.y
        displacement = np.sqrt(dx**2 + dy**2)
        displacements.append(displacement)
    
    return displacements


def calculate_velocity(displacements: List[float], delta_t: float) -> List[float]:
    """
    Calculate velocity from displacements.
    
    Args:
        displacements: List of displacement values
        delta_t: Time difference between frames
        
    Returns:
        List of velocity values
    """
    if not displacements or delta_t == 0:
        return []
    
    velocities = [displacement / delta_t for displacement in displacements]
    return velocities


def calculate_acceleration(velocities_current: List[float], velocities_previous: List[float], delta_t: float) -> List[float]:
    """
    Calculate acceleration from velocities.
    
    Args:
        velocities_current: Current frame velocities
        velocities_previous: Previous frame velocities
        delta_t: Time difference between frames
        
    Returns:
        List of acceleration values
    """
    if not velocities_current or not velocities_previous or delta_t == 0:
        return []
    
    if len(velocities_current) != len(velocities_previous):
        return []
    
    accelerations = []
    for curr_vel, prev_vel in zip(velocities_current, velocities_previous):
        acceleration = (curr_vel - prev_vel) / delta_t
        accelerations.append(acceleration)
    
    return accelerations


def calculate_direction_change(keypoints_t2: List[Keypoint], keypoints_t1: List[Keypoint], keypoints_t0: List[Keypoint]) -> List[float]:
    """
    Calculate direction change between consecutive frames.
    
    Args:
        keypoints_t2: Keypoints at time t+2
        keypoints_t1: Keypoints at time t+1
        keypoints_t0: Keypoints at time t
        
    Returns:
        List of direction change values (in radians)
    """
    if not keypoints_t2 or not keypoints_t1 or not keypoints_t0:
        return []
    
    if len(keypoints_t2) != len(keypoints_t1) or len(keypoints_t1) != len(keypoints_t0):
        return []
    
    direction_changes = []
    
    for kp2, kp1, kp0 in zip(keypoints_t2, keypoints_t1, keypoints_t0):
        # Calculate vectors
        vec1 = np.array([kp1.x - kp0.x, kp1.y - kp0.y])
        vec2 = np.array([kp2.x - kp1.x, kp2.y - kp1.y])
        
        # Calculate magnitudes
        mag1 = np.linalg.norm(vec1)
        mag2 = np.linalg.norm(vec2)
        
        # If either vector has zero magnitude, no direction change
        if mag1 == 0 or mag2 == 0:
            direction_changes.append(0.0)
            continue
        
        # Normalize vectors
        vec1_norm = vec1 / mag1
        vec2_norm = vec2 / mag2
        
        # Calculate angle between vectors using dot product
        dot_product = np.clip(np.dot(vec1_norm, vec2_norm), -1.0, 1.0)
        angle = np.arccos(dot_product)
        
        direction_changes.append(angle)
    
    return direction_changes


def calculate_pose_change(keypoints_current: List[Keypoint], keypoints_previous: List[Keypoint]) -> float:
    """
    Calculate pose change between two sets of keypoints.
    
    Args:
        keypoints_current: Current frame keypoints
        keypoints_previous: Previous frame keypoints
        
    Returns:
        Pose change value (normalized)
    """
    if not keypoints_current or not keypoints_previous:
        return 0.0
    
    if len(keypoints_current) != len(keypoints_previous):
        return 0.0
    
    # Calculate the sum of squared distances between corresponding keypoints
    total_distance = 0.0
    for curr, prev in zip(keypoints_current, keypoints_previous):
        dx = curr.x - prev.x
        dy = curr.y - prev.y
        distance = np.sqrt(dx**2 + dy**2)
        total_distance += distance
    
    # Normalize by the number of keypoints
    if len(keypoints_current) > 0:
        pose_change = total_distance / len(keypoints_current)
    else:
        pose_change = 0.0
    
    return pose_change


def calculate_motion_intensity_score(
    displacement: List[float],
    velocity: List[float], 
    acceleration: List[float],
    direction_change: List[float],
    pose_change: float,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate the overall motion intensity score.
    
    Args:
        displacement: List of displacement values
        velocity: List of velocity values
        acceleration: List of acceleration values
        direction_change: List of direction change values
        pose_change: Pose change value
        weights: Optional weights for each component
        
    Returns:
        Motion intensity score (0.0 to 1.0)
    """
    # Default weights if not provided
    if weights is None:
        weights = {
            'displacement': 0.2,
            'velocity': 0.25,
            'acceleration': 0.25,
            'direction_change': 0.15,
            'pose_change': 0.15
        }
    
    # Handle empty data
    if not displacement and not velocity and not acceleration and not direction_change and pose_change == 0.0:
        return 0.0
    
    # Calculate normalized components
    components = {}
    
    # Displacement component
    if displacement:
        components['displacement'] = np.mean(displacement)
    else:
        components['displacement'] = 0.0
    
    # Velocity component
    if velocity:
        components['velocity'] = np.mean(velocity)
    else:
        components['velocity'] = 0.0
    
    # Acceleration component
    if acceleration:
        components['acceleration'] = np.mean(np.abs(acceleration))
    else:
        components['acceleration'] = 0.0
    
    # Direction change component
    if direction_change:
        components['direction_change'] = np.mean(direction_change)
    else:
        components['direction_change'] = 0.0
    
    # Pose change component
    components['pose_change'] = pose_change
    
    # Normalize each component to 0-1 range
    # These normalization factors are heuristic and may need adjustment based on real data
    normalization_factors = {
        'displacement': 50.0,  # Typical max displacement in pixels
        'velocity': 1000.0,    # Typical max velocity in pixels/second
        'acceleration': 10000.0,  # Typical max acceleration
        'direction_change': np.pi,  # Max direction change is π radians
        'pose_change': 100.0   # Typical max pose change
    }
    
    normalized_components = {}
    for component, value in components.items():
        normalized_value = min(value / normalization_factors[component], 1.0)
        normalized_components[component] = normalized_value
    
    # Calculate weighted sum
    intensity_score = 0.0
    for component, weight in weights.items():
        if component in normalized_components:
            intensity_score += weight * normalized_components[component]
    
    # Ensure the score is between 0 and 1
    intensity_score = max(0.0, min(1.0, intensity_score))
    
    return intensity_score