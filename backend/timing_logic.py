"""
Timing logic module for 2D animation frame timing decisions.

This module implements hysteresis-based motion state classification and frame timing
decisions for 2D animation processing.
"""

import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any


class MotionState(Enum):
    """Motion state classification for animation frames."""
    LOW = "LOW"
    MID = "MID" 
    HIGH = "HIGH"
    
    @property
    def frame_hold_count(self) -> int:
        """Get the frame hold count for this motion state."""
        if self == MotionState.LOW:
            return 1  # Hold all frames (no frame dropping)
        elif self == MotionState.MID:
            return 3  # 3-frame timing
        elif self == MotionState.HIGH:
            return 2  # 2-frame timing
        else:
            return 1


@dataclass
class FrameTimingDecision:
    """Represents a timing decision for a single frame."""
    frame_index: int
    motion_state: MotionState
    should_keep: bool
    timing_multiplier: int
    is_tame: bool = False  # Anticipation/hold frame
    is_tsume: bool = False  # Impact/acceleration frame
    
    @classmethod
    def from_motion_states(cls, motion_states: List[MotionState], start_frame: int = 0) -> List['FrameTimingDecision']:
        """Create timing decisions from a list of motion states."""
        decisions = []
        for i, state in enumerate(motion_states):
            decision = cls(
                frame_index=start_frame + i,
                motion_state=state,
                should_keep=True,  # All frames are kept, timing is adjusted
                timing_multiplier=state.frame_hold_count
            )
            decisions.append(decision)
        return decisions


class HysteresisProcessor:
    """Processes motion intensity scores with hysteresis to prevent flickering."""
    
    def __init__(self, 
                 high_threshold: float = 0.60,
                 low_threshold: float = 0.35,
                 hysteresis_margin: float = 0.05):
        """
        Initialize hysteresis processor.
        
        Args:
            high_threshold: Threshold for HIGH motion state
            low_threshold: Threshold for LOW motion state  
            hysteresis_margin: Margin for hysteresis transitions
        """
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.hysteresis_margin = hysteresis_margin
    
    def process_frame(self, motion_intensity: float, previous_state: Optional[MotionState]) -> MotionState:
        """
        Process a single frame's motion intensity with hysteresis.
        
        Args:
            motion_intensity: Motion intensity score (0.0 to 1.0)
            previous_state: Previous frame's motion state (None for first frame)
            
        Returns:
            Motion state for this frame
        """
        if previous_state is None:
            # Initial classification without hysteresis
            return self._classify_initial_state(motion_intensity)
        
        # Apply hysteresis based on previous state
        return self._classify_with_hysteresis(motion_intensity, previous_state)
    
    def _classify_initial_state(self, motion_intensity: float) -> MotionState:
        """Classify motion state without previous context."""
        if motion_intensity >= self.high_threshold:
            return MotionState.HIGH
        elif motion_intensity >= self.low_threshold:
            return MotionState.MID
        else:
            return MotionState.LOW
    
    def _classify_with_hysteresis(self, motion_intensity: float, previous_state: MotionState) -> MotionState:
        """Classify motion state with hysteresis based on previous state."""
        if previous_state == MotionState.HIGH:
            # From HIGH state
            if motion_intensity < self.low_threshold:
                return MotionState.LOW  # Direct transition to LOW
            elif motion_intensity < (self.high_threshold - self.hysteresis_margin):
                return MotionState.MID  # Hysteresis transition to MID (0.55)
            else:
                return MotionState.HIGH  # Stay in HIGH
                
        elif previous_state == MotionState.MID:
            # From MID state
            if motion_intensity >= (self.high_threshold + self.hysteresis_margin):
                return MotionState.HIGH  # Hysteresis transition to HIGH (0.65)
            elif motion_intensity < (self.low_threshold - self.hysteresis_margin):
                return MotionState.LOW  # Hysteresis transition to LOW (0.30)
            else:
                return MotionState.MID  # Stay in MID
                
        elif previous_state == MotionState.LOW:
            # From LOW state
            if motion_intensity >= (self.high_threshold + self.hysteresis_margin):
                return MotionState.HIGH  # Direct transition to HIGH (0.65)
            elif motion_intensity >= (self.low_threshold + self.hysteresis_margin):
                return MotionState.MID  # Hysteresis transition to MID (0.40)
            else:
                return MotionState.LOW  # Stay in LOW
        
        return previous_state  # Fallback


def smooth_motion_intensity(mi_scores: List[float], 
                          method: str = "ema", 
                          alpha: float = 0.3,
                          window_size: int = 3) -> List[float]:
    """
    Smooth motion intensity scores to reduce noise.
    
    Args:
        mi_scores: List of motion intensity scores
        method: Smoothing method ("ema" or "window")
        alpha: Alpha parameter for EMA smoothing
        window_size: Window size for window-based smoothing
        
    Returns:
        Smoothed motion intensity scores
    """
    if not mi_scores:
        return []
    
    if method == "ema":
        # Exponential moving average
        smoothed = [mi_scores[0]]  # First value unchanged
        for i in range(1, len(mi_scores)):
            smoothed_value = alpha * mi_scores[i] + (1 - alpha) * smoothed[i-1]
            smoothed.append(smoothed_value)
        return smoothed
        
    elif method == "window":
        # Window-based smoothing
        smoothed = []
        for i in range(len(mi_scores)):
            if i == 0:
                # First value unchanged
                smoothed.append(mi_scores[0])
            else:
                # Use a window from start to current index + 1, limited by window_size
                start_idx = max(0, i + 1 - window_size)
                end_idx = i + 1
                window_values = mi_scores[start_idx:end_idx]
                smoothed_value = np.mean(window_values)
                smoothed.append(smoothed_value)
        return smoothed
        
    else:
        raise ValueError(f"Unknown smoothing method: {method}")


def apply_minimum_duration_constraint(states: List[MotionState], 
                                    timestamps: List[float],
                                    min_duration: float = 0.08) -> List[MotionState]:
    """
    Apply minimum duration constraint to motion states.
    
    Args:
        states: List of motion states
        timestamps: List of frame timestamps
        min_duration: Minimum duration for state segments (seconds)
        
    Returns:
        Constrained motion states
    """
    if len(states) != len(timestamps) or len(states) <= 1:
        return states
    
    constrained_states = states.copy()
    
    # Find state segments
    segments = []
    current_state = states[0]
    segment_start = 0
    
    for i in range(1, len(states)):
        if states[i] != current_state:
            segments.append((segment_start, i-1, current_state))
            current_state = states[i]
            segment_start = i
    
    # Add final segment
    segments.append((segment_start, len(states)-1, current_state))
    
    # Check and fix short segments
    for start_idx, end_idx, state in segments:
        segment_duration = timestamps[end_idx] - timestamps[start_idx]
        
        if segment_duration < min_duration:
            # Only apply constraint to MID and LOW states, not HIGH states
            # HIGH states are important for animation timing even if short
            if state != MotionState.HIGH:
                # Revert short segments to previous state
                if start_idx > 0:
                    prev_state = constrained_states[start_idx - 1]
                    for i in range(start_idx, end_idx + 1):
                        constrained_states[i] = prev_state
    
    return constrained_states


def detect_tame_tsume(accelerations: List[float], 
                     mi_scores: List[float],
                     acceleration_threshold: float = 0.5) -> Tuple[List[int], List[int]]:
    """
    Detect tame (anticipation/hold) and tsume (impact/acceleration) frames.
    
    Args:
        accelerations: List of acceleration values
        mi_scores: List of motion intensity scores
        acceleration_threshold: Threshold for detecting acceleration spikes
        
    Returns:
        Tuple of (tame_frames, tsume_frames) - lists of frame indices
    """
    if len(accelerations) != len(mi_scores) or len(accelerations) == 0:
        return [], []
    
    tame_frames = []
    tsume_frames = []
    
    # Detect acceleration spikes (tsume)
    for i, accel in enumerate(accelerations):
        if accel >= acceleration_threshold:
            tsume_frames.append(i)
    
    # Detect tame frames (low motion before acceleration)
    for tsume_frame in tsume_frames:
        # Look for low motion frames before tsume
        for j in range(max(0, tsume_frame - 3), tsume_frame):
            if mi_scores[j] < 0.3:  # Low motion threshold
                tame_frames.append(j)
    
    return tame_frames, tsume_frames


class TimingLogicProcessor:
    """Main processor for timing logic decisions."""
    
    def __init__(self,
                 high_threshold: float = 0.60,
                 low_threshold: float = 0.35,
                 hysteresis_margin: float = 0.05,
                 min_duration: float = 0.08,
                 smoothing_method: str = "ema",
                 smoothing_alpha: float = 0.7,
                 enable_tame_tsume: bool = False):
        """
        Initialize timing logic processor.
        
        Args:
            high_threshold: Threshold for HIGH motion state
            low_threshold: Threshold for LOW motion state
            hysteresis_margin: Margin for hysteresis transitions
            min_duration: Minimum duration for state segments
            smoothing_method: Method for smoothing motion intensity
            smoothing_alpha: Alpha parameter for EMA smoothing
            enable_tame_tsume: Whether to enable tame/tsume detection
        """
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.hysteresis_margin = hysteresis_margin
        self.min_duration = min_duration
        self.smoothing_method = smoothing_method
        self.smoothing_alpha = smoothing_alpha
        self.enable_tame_tsume = enable_tame_tsume
        
        self.hysteresis_processor = HysteresisProcessor(
            high_threshold, low_threshold, hysteresis_margin
        )
    
    def process_sequence(self, 
                        mi_scores: List[float], 
                        timestamps: List[float],
                        accelerations: Optional[List[float]] = None) -> List[FrameTimingDecision]:
        """
        Process a complete sequence of motion intensity scores.
        
        Args:
            mi_scores: List of motion intensity scores
            timestamps: List of frame timestamps
            accelerations: Optional list of acceleration values for tame/tsume detection
            
        Returns:
            List of frame timing decisions
        """
        if len(mi_scores) != len(timestamps):
            raise ValueError("Motion intensity scores and timestamps must have same length")
        
        # Smooth motion intensity scores
        smoothed_scores = smooth_motion_intensity(
            mi_scores, 
            method=self.smoothing_method,
            alpha=self.smoothing_alpha
        )
        
        # Apply hysteresis to get motion states
        motion_states = []
        previous_state = None
        
        for score in smoothed_scores:
            state = self.hysteresis_processor.process_frame(score, previous_state)
            motion_states.append(state)
            previous_state = state
        
        # Apply minimum duration constraint
        constrained_states = apply_minimum_duration_constraint(
            motion_states, timestamps, self.min_duration
        )
        
        # Create timing decisions
        decisions = FrameTimingDecision.from_motion_states(constrained_states)
        
        # Apply tame/tsume detection if enabled
        if self.enable_tame_tsume and accelerations:
            tame_frames, tsume_frames = detect_tame_tsume(
                accelerations, smoothed_scores
            )
            
            # Mark tame and tsume frames
            for decision in decisions:
                if decision.frame_index in tame_frames:
                    decision.is_tame = True
                if decision.frame_index in tsume_frames:
                    decision.is_tsume = True
        
        return decisions