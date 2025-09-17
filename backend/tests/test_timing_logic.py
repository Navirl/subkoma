import pytest
import numpy as np
from typing import List, Dict, Any
from backend.timing_logic import (
    MotionState,
    HysteresisProcessor,
    FrameTimingDecision,
    TimingLogicProcessor,
    smooth_motion_intensity,
    detect_tame_tsume,
    apply_minimum_duration_constraint
)


class TestMotionState:
    """Test the MotionState enum and its properties."""
    
    def test_motion_state_values(self):
        """Test that MotionState enum has correct values."""
        assert MotionState.LOW.value == "LOW"
        assert MotionState.MID.value == "MID" 
        assert MotionState.HIGH.value == "HIGH"
    
    def test_motion_state_frame_counts(self):
        """Test that each motion state has correct frame timing."""
        assert MotionState.LOW.frame_hold_count == 1  # Hold all frames
        assert MotionState.MID.frame_hold_count == 3  # 3-frame timing
        assert MotionState.HIGH.frame_hold_count == 2  # 2-frame timing


class TestHysteresisProcessor:
    """Test the hysteresis logic for state transitions."""
    
    def test_initial_state_classification(self):
        """Test initial state classification without previous state."""
        processor = HysteresisProcessor()
        
        # HIGH threshold (>= 0.60)
        assert processor.process_frame(0.65, None) == MotionState.HIGH
        assert processor.process_frame(0.60, None) == MotionState.HIGH
        
        # MID threshold (>= 0.35, < 0.60)
        assert processor.process_frame(0.50, None) == MotionState.MID
        assert processor.process_frame(0.35, None) == MotionState.MID
        
        # LOW threshold (< 0.35)
        assert processor.process_frame(0.30, None) == MotionState.LOW
        assert processor.process_frame(0.10, None) == MotionState.LOW
    
    def test_hysteresis_from_high_state(self):
        """Test state transitions from HIGH state with hysteresis."""
        processor = HysteresisProcessor()
        
        # HIGH -> HIGH (maintain)
        assert processor.process_frame(0.60, MotionState.HIGH) == MotionState.HIGH
        assert processor.process_frame(0.55, MotionState.HIGH) == MotionState.HIGH
        
        # HIGH -> MID (hysteresis threshold 0.55)
        assert processor.process_frame(0.54, MotionState.HIGH) == MotionState.MID
        assert processor.process_frame(0.40, MotionState.HIGH) == MotionState.MID
        
        # HIGH -> LOW (direct transition < 0.30)
        assert processor.process_frame(0.29, MotionState.HIGH) == MotionState.LOW
        assert processor.process_frame(0.10, MotionState.HIGH) == MotionState.LOW
    
    def test_hysteresis_from_mid_state(self):
        """Test state transitions from MID state with hysteresis."""
        processor = HysteresisProcessor()
        
        # MID -> HIGH (hysteresis threshold 0.65)
        assert processor.process_frame(0.65, MotionState.MID) == MotionState.HIGH
        assert processor.process_frame(0.70, MotionState.MID) == MotionState.HIGH
        
        # MID -> MID (maintain)
        assert processor.process_frame(0.64, MotionState.MID) == MotionState.MID
        assert processor.process_frame(0.40, MotionState.MID) == MotionState.MID
        assert processor.process_frame(0.30, MotionState.MID) == MotionState.MID
        
        # MID -> LOW (hysteresis threshold < 0.30)
        assert processor.process_frame(0.29, MotionState.MID) == MotionState.LOW
        assert processor.process_frame(0.15, MotionState.MID) == MotionState.LOW
    
    def test_hysteresis_from_low_state(self):
        """Test state transitions from LOW state with hysteresis."""
        processor = HysteresisProcessor()
        
        # LOW -> LOW (maintain)
        assert processor.process_frame(0.39, MotionState.LOW) == MotionState.LOW
        assert processor.process_frame(0.20, MotionState.LOW) == MotionState.LOW
        
        # LOW -> MID (hysteresis threshold 0.40)
        assert processor.process_frame(0.40, MotionState.LOW) == MotionState.MID
        assert processor.process_frame(0.50, MotionState.LOW) == MotionState.MID
        
        # LOW -> HIGH (direct transition >= 0.65)
        assert processor.process_frame(0.65, MotionState.LOW) == MotionState.HIGH
        assert processor.process_frame(0.80, MotionState.LOW) == MotionState.HIGH


class TestSmoothingFunctions:
    """Test motion intensity smoothing functions."""
    
    def test_smooth_motion_intensity_ema(self):
        """Test exponential moving average smoothing."""
        mi_scores = [0.1, 0.5, 0.8, 0.3, 0.6]
        alpha = 0.3
        
        smoothed = smooth_motion_intensity(mi_scores, method="ema", alpha=alpha)
        
        # Should return same length
        assert len(smoothed) == len(mi_scores)
        
        # First value should be unchanged
        assert smoothed[0] == mi_scores[0]
        
        # Subsequent values should be smoothed
        expected_1 = alpha * mi_scores[1] + (1 - alpha) * smoothed[0]
        assert abs(smoothed[1] - expected_1) < 1e-6
    
    def test_smooth_motion_intensity_window(self):
        """Test window-based smoothing."""
        mi_scores = [0.1, 0.5, 0.8, 0.3, 0.6, 0.2, 0.7]
        window_size = 3
        
        smoothed = smooth_motion_intensity(mi_scores, method="window", window_size=window_size)
        
        # Should return same length
        assert len(smoothed) == len(mi_scores)
        
        # First few values should be unchanged or partially smoothed
        assert smoothed[0] == mi_scores[0]
        
        # Middle values should be averaged
        expected_2 = np.mean(mi_scores[0:3])
        assert abs(smoothed[2] - expected_2) < 1e-6
    
    def test_smooth_motion_intensity_invalid_method(self):
        """Test that invalid smoothing method raises error."""
        mi_scores = [0.1, 0.5, 0.8]
        
        with pytest.raises(ValueError, match="Unknown smoothing method"):
            smooth_motion_intensity(mi_scores, method="invalid")


class TestMinimumDurationConstraint:
    """Test minimum duration constraint logic."""
    
    def test_apply_minimum_duration_constraint(self):
        """Test that short state segments are extended to minimum duration."""
        states = [MotionState.LOW, MotionState.HIGH, MotionState.HIGH, MotionState.LOW, MotionState.LOW]
        timestamps = [0.0, 0.03, 0.06, 0.09, 0.12]  # 30fps, 0.033s per frame
        min_duration = 0.08  # 80ms minimum
        
        constrained_states = apply_minimum_duration_constraint(states, timestamps, min_duration)
        
        # Should return same length
        assert len(constrained_states) == len(states)
        
        # Short HIGH segment (0.03s) should be extended or reverted
        # This is a failing test - implementation should handle this
        assert constrained_states != states  # Should be different due to constraint
    
    def test_minimum_duration_with_sufficient_length(self):
        """Test that segments meeting minimum duration are unchanged."""
        states = [MotionState.LOW] * 5 + [MotionState.HIGH] * 5 + [MotionState.LOW] * 5
        timestamps = [i * 0.033 for i in range(15)]  # Each segment is ~0.165s
        min_duration = 0.08
        
        constrained_states = apply_minimum_duration_constraint(states, timestamps, min_duration)
        
        # Should be unchanged since all segments are long enough
        assert constrained_states == states


class TestTameTsumeDetection:
    """Test Tame (hold) and Tsume (squeeze) detection logic."""
    
    def test_detect_tame_tsume_basic(self):
        """Test basic tame/tsume detection from acceleration patterns."""
        # Simulate acceleration pattern: low -> high (tsume start)
        accelerations = [0.1, 0.1, 0.8, 0.9, 0.2, 0.1]
        mi_scores = [0.2, 0.2, 0.7, 0.8, 0.3, 0.2]
        acceleration_threshold = 0.5
        
        tame_frames, tsume_frames = detect_tame_tsume(accelerations, mi_scores, acceleration_threshold)
        
        # Should detect tsume start around frame 2-3
        assert len(tsume_frames) > 0
        assert 2 in tsume_frames or 3 in tsume_frames
        
        # Should detect tame before tsume
        assert len(tame_frames) > 0
        assert min(tame_frames) < min(tsume_frames)
    
    def test_detect_tame_tsume_no_pattern(self):
        """Test tame/tsume detection with no clear pattern."""
        # Uniform low acceleration
        accelerations = [0.1, 0.1, 0.1, 0.1, 0.1]
        mi_scores = [0.2, 0.2, 0.2, 0.2, 0.2]
        acceleration_threshold = 0.5
        
        tame_frames, tsume_frames = detect_tame_tsume(accelerations, mi_scores, acceleration_threshold)
        
        # Should not detect any tame/tsume
        assert len(tame_frames) == 0
        assert len(tsume_frames) == 0


class TestFrameTimingDecision:
    """Test frame timing decision logic."""
    
    def test_frame_timing_decision_creation(self):
        """Test FrameTimingDecision object creation."""
        decision = FrameTimingDecision(
            frame_index=10,
            motion_state=MotionState.HIGH,
            should_keep=True,
            timing_multiplier=2
        )
        
        assert decision.frame_index == 10
        assert decision.motion_state == MotionState.HIGH
        assert decision.should_keep is True
        assert decision.timing_multiplier == 2
    
    def test_frame_timing_decision_from_motion_state(self):
        """Test creating timing decisions from motion states."""
        # This should be implemented in timing_logic.py
        decisions = FrameTimingDecision.from_motion_states(
            [MotionState.HIGH, MotionState.MID, MotionState.LOW],
            start_frame=0
        )
        
        assert len(decisions) == 3
        assert decisions[0].motion_state == MotionState.HIGH
        assert decisions[0].timing_multiplier == 2
        assert decisions[1].motion_state == MotionState.MID
        assert decisions[1].timing_multiplier == 3
        assert decisions[2].motion_state == MotionState.LOW
        assert decisions[2].timing_multiplier == 1


class TestTimingLogicProcessor:
    """Test the main timing logic processor."""
    
    def test_timing_logic_processor_initialization(self):
        """Test TimingLogicProcessor initialization with parameters."""
        params = {
            'high_threshold': 0.60,
            'low_threshold': 0.35,
            'hysteresis_margin': 0.05,
            'min_duration': 0.08,
            'smoothing_method': 'ema',
            'smoothing_alpha': 0.3
        }
        
        processor = TimingLogicProcessor(**params)
        
        assert processor.high_threshold == 0.60
        assert processor.low_threshold == 0.35
        assert processor.hysteresis_margin == 0.05
        assert processor.min_duration == 0.08
    
    def test_process_motion_intensity_sequence(self):
        """Test processing a complete motion intensity sequence."""
        processor = TimingLogicProcessor()
        
        # Simulate a motion sequence: low -> high -> low
        mi_scores = [0.2, 0.3, 0.7, 0.8, 0.6, 0.3, 0.2]
        timestamps = [i * 0.033 for i in range(len(mi_scores))]
        
        decisions = processor.process_sequence(mi_scores, timestamps)
        
        # Should return timing decisions for each frame
        assert len(decisions) == len(mi_scores)
        
        # Should have different motion states
        states = [d.motion_state for d in decisions]
        assert MotionState.LOW in states
        assert MotionState.HIGH in states
    
    def test_process_with_tame_tsume_detection(self):
        """Test processing with tame/tsume detection enabled."""
        processor = TimingLogicProcessor(enable_tame_tsume=True)
        
        # Simulate motion with acceleration pattern
        mi_scores = [0.2, 0.2, 0.7, 0.8, 0.3, 0.2]
        timestamps = [i * 0.033 for i in range(len(mi_scores))]
        accelerations = [0.1, 0.1, 0.8, 0.9, 0.2, 0.1]
        
        decisions = processor.process_sequence(
            mi_scores, 
            timestamps, 
            accelerations=accelerations
        )
        
        # Should detect and mark tame/tsume frames
        tame_decisions = [d for d in decisions if hasattr(d, 'is_tame') and d.is_tame]
        tsume_decisions = [d for d in decisions if hasattr(d, 'is_tsume') and d.is_tsume]
        
        # This test should fail until implementation is complete
        assert len(tame_decisions) > 0 or len(tsume_decisions) > 0


class TestIntegrationScenarios:
    """Integration tests for complete timing logic scenarios."""
    
    def test_complete_animation_sequence(self):
        """Test processing a complete animation sequence."""
        # Simulate a typical 2D animation sequence
        # Idle -> action -> idle pattern
        mi_scores = (
            [0.1] * 10 +  # Idle start
            [0.2, 0.4, 0.7, 0.9, 0.8, 0.6, 0.4, 0.2] +  # Action sequence
            [0.1] * 10   # Idle end
        )
        timestamps = [i * 0.033 for i in range(len(mi_scores))]
        
        processor = TimingLogicProcessor()
        decisions = processor.process_sequence(mi_scores, timestamps)
        
        # Should have appropriate state transitions
        states = [d.motion_state for d in decisions]
        
        # Should start and end with LOW state
        assert states[0] == MotionState.LOW
        assert states[-1] == MotionState.LOW
        
        # Should have HIGH state during action
        assert MotionState.HIGH in states[10:18]
    
    def test_flickering_prevention(self):
        """Test that hysteresis prevents rapid state flickering."""
        # Simulate noisy MI scores around threshold
        mi_scores = [0.58, 0.62, 0.58, 0.63, 0.57, 0.61]
        timestamps = [i * 0.033 for i in range(len(mi_scores))]
        
        processor = TimingLogicProcessor()
        decisions = processor.process_sequence(mi_scores, timestamps)
        
        states = [d.motion_state for d in decisions]
        
        # Should not rapidly alternate between states
        # Count state changes
        state_changes = sum(1 for i in range(1, len(states)) if states[i] != states[i-1])
        
        # Should have fewer state changes than without hysteresis
        assert state_changes < len(states) - 1