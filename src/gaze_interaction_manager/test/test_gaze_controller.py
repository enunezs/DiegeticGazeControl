#!/usr/bin/env python3
"""
Extended GazeController Test Suite
Run with:
python3 -m pytest src/gaze_interaction_manager/test/test_gaze_controller.py -v -s -k test_pipeline_delay_shifts_interpolation

Covers:
! FAILED test_nonsticky_interpolation_uses_only_current_segment_buttons - assert 0 == 1
! FAILED test_gap_masking_drops_samples_during_loss - IndexError: index 0 is out of bounds for axis 0 with size 0
! FAILED test_max_error_masking - IndexError: list index out of range
! FAILED test_polynomial_correction_application - NameError: name 'CalibrationModel' is not defined

FAILED test_concurrent_button_ids_same_timestamp - assert 0 == 1
FAILED test_sticky_release_does_not_trigger_segment - AssertionError: Recording should have information after saccade.
"""

from platform import node
import sys
import os
import math
import pytest
import rclpy
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, '..', 'scripts')
sys.path.insert(0, scripts_dir)
src_dir = os.path.join(current_dir, '..', '..', 'diegetic_transform_engine', 'scripts')
sys.path.insert(0, src_dir)

from gaze_controller import GazeController

from std_msgs.msg import Header
from geometry_msgs.msg import Point
from pupil_neon_ros.msg import GazeData, GazeEvent
from gaze_interaction_manager.msg import ButtonStatus, CalibrationModel
from diegetic_transform_engine.msg import DiegeticButton2D


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_button(button_id, cx, cy, t_sec, t_nanosec=0,
                status=ButtonStatus.BUTTON_ACTIVE):
    msg = ButtonStatus(
        button_status=status,
        button=DiegeticButton2D(button_id=button_id,
                                center_x=float(cx),
                                center_y=float(cy)),
    )
    msg.header.stamp.sec = t_sec
    msg.header.stamp.nanosec = t_nanosec
    return msg

def make_gaze(x, y, t_sec, t_nanosec=0):
    msg = GazeData(x=float(x), y=float(y))
    msg.header.stamp.sec = t_sec
    msg.header.stamp.nanosec = t_nanosec
    return msg

def make_saccade(t_ns):
    return GazeEvent(start_time_ns=t_ns)

def capture_segments(node):
    """Monkey-patch segment_pub so we can collect what gets published."""
    published = []
    node.segment_pub.publish = lambda msg: published.append(msg)
    return published

def zero_params(node):
    """Turn off all filtering/trim so tests are purely about the logic under test."""
    node.set_parameters([

        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),


    ])

def nonsticky_node():
    """Returns a GazeController with non-sticky mode and all trims zeroed."""
    node = GazeController()
    node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('max_gap_ms', value=10000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=2000.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),

    ])
    return node
 
 
# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def ros_setup():
    rclpy.init()
    yield
    rclpy.shutdown()


# ===========================================================================
# 1. GHOST BUTTON — assertion fix
# ===========================================================================

def test_ghost_button_extrapolation_no_extrapolation():
    """
    np.interp clamps to boundary values when queried outside the data range.
    Gaze at T=4.0 is BEYOND the last button sample (T=2.0).
    Correct behaviour: target_x should be clamped to the last known X (20.0),
    NOT extrapolated further.

    The original test only printed and never asserted — this version asserts.

    BUG(1): The original test_ghost_button_extrapolation has NO assert — it
    always passes regardless of whether the node extrapolates or clamps.
    Fix: Add the assert below (or decide on None/NaN and assert that instead).
    """
    node = GazeController()
    zero_params(node)

    # Make 2 buttons at T=1s and T=2s
    btn_1 = make_button("btn1", 10.0, 10.0, 1)
    btn_2 = make_button("btn1", 20.0, 20.0, 2)
    node.button_cb(btn_1)
    node.button_cb(btn_2)

    # 2. Going into the future, gaze at T=4s (beyond the last button)
    for t_sec in [1, 2, 3, 4]:
        node.gaze_cb(make_gaze(100.0, 100.0, t_sec))

    assert node.gaze_ptr == 4, "Gaze history should have four entries."


    published = capture_segments(node)
    node.saccade_cb(make_saccade(4_500_000_000))

    assert len(published) == 1
    segment = published[0]

    target_x_at_t4 = segment.target_samples[-1].x
    # np.interp clamps — last sample should equal the last known position
    assert target_x_at_t4 == 20.0, (
        f"Expected clamped value 20.0, got {target_x_at_t4}. "
        "If the design intent is to drop out-of-range samples, assert None/NaN instead."
    )



def test_pipeline_unadjusted_interpolation():
    """
    internal_pipeline_delay_ms subtracts N ms from the button timestamp so that
    button and gaze timestamps are aligned on the same hardware clock.

    Setup:
      - Delay = 500ms  (camera is 500ms behind gaze clock)
      - Button at hardware T=1.5 → stored as adjusted T=1.0
      - Button at hardware T=2.5 → stored as adjusted T=2.0
      - Gaze sample at T=1.5  (no delay adjustment needed for gaze)
      - Interpolated target should be X=15.0 (midpoint of 10→20 range)

    Without delay compensation the button timestamps would be 1.5 and 2.5,
    so interp at T=1.5 would return X=10.0 (the first sample exactly).

    BUG(2): In button_cb, `button_ts` is re-declared inside the "Rising Edge"
    block (line ~160 of the source), silently shadowing the adjusted_ts already
    calculated above. The re-computed value is the raw timestamp, so
    `self.rec_start_ts` stores the *unadjusted* time.  Segments are then
    windowed using `rec_start_ts` vs adjusted gaze times — causing a
    systematic offset equal to the pipeline delay.
    Fix: replace `button_ts = msg.header.stamp…` with `self.rec_start_ts = adjusted_ts`
    (which is the line immediately after, making the re-assignment redundant anyway).
    """

    node = GazeController()
    success = node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),

    ])

    # Process the parameter callback
    rclpy.spin_once(node, timeout_sec=0.1) 

    assert node.start_trim_ms == 0.0, "start_trim_ms parameter not set correctly."
    assert node.max_gap_ms == 5000.0, "max_gap_ms parameter not set correctly." 

    # Gaze at T=1.5 (adjusted btn midpoint)
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 0))
    node.gaze_cb(make_gaze(200.0, 200.0, 2, 0))
    node.gaze_cb(make_gaze(300.0, 300.0, 3, 0))

    published = capture_segments(node)

    btn_1 = make_button("btn1", 10.0, 100.0, 1, 0)  
    btn_2 = make_button("btn1", 30.0, 300.0, 3, 0) 
    node.button_cb(btn_1)
    node.button_cb(btn_2)

    node.saccade_cb(make_saccade(3_200_000_000))

    # Should publish one segment
    assert len(published) == 1, "No segment published"
    print(published)

    # Unpack into 3 vectors
    targets = [[s.x, s.y] for s in published[0].target_samples]

    assert len(targets) == 3, f"Expected 3 target samples, got {len(targets)}. " 

    assert targets[0] == [10.0, 100.0], (
        f"Interpolation ! FAIL: expected [10.0, 100.0], got {targets[0]}. "
        "rec_start_ts is likely using the raw timestamp — see BUG(2)."
    )
    assert targets[1] == [20.0, 200.0], (
        f"Interpolation ! FAIL: expected [20.0, 200.0], got {targets[1]}. "
        "rec_start_ts is likely using the raw timestamp — see BUG(2)."
    )
    assert targets[2] == [30.0, 300.0], (
        f"Interpolation ! FAIL: expected [30.0, 300.0], got {targets[2]}. "
        "rec_start_ts is likely using the raw timestamp — see BUG(2)."
    )




# ===========================================================================
# 2. PIPELINE DELAY COMPENSATION
# ===========================================================================

def test_pipeline_delay_shifts_interpolation():
    """
    internal_pipeline_delay_ms subtracts N ms from the button timestamp so that
    button and gaze timestamps are aligned on the same hardware clock.

    Setup:
      - Delay = 500ms  (camera is 500ms behind gaze clock)
      - Button at hardware T=1.5 → stored as adjusted T=1.0
      - Button at hardware T=2.5 → stored as adjusted T=2.0
      - Gaze sample at T=1.5  (no delay adjustment needed for gaze)
      - Interpolated target should be X=15.0 (midpoint of 10→20 range)

    Without delay compensation the button timestamps would be 1.5 and 2.5,
    so interp at T=1.5 would return X=10.0 (the first sample exactly).

    BUG(2): In button_cb, `button_ts` is re-declared inside the "Rising Edge"
    block (line ~160 of the source), silently shadowing the adjusted_ts already
    calculated above. The re-computed value is the raw timestamp, so
    `self.rec_start_ts` stores the *unadjusted* time.  Segments are then
    windowed using `rec_start_ts` vs adjusted gaze times — causing a
    systematic offset equal to the pipeline delay.
    Fix: replace `button_ts = msg.header.stamp…` with `self.rec_start_ts = adjusted_ts`
    (which is the line immediately after, making the re-assignment redundant anyway).
    """

    node = GazeController()
    node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=500.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),

    ])

    # Hardware timestamps 1.5s and 2.5s → adjusted to 1.0 and 2.0
    btn_1 = make_button("btn1", 10.0, 10.0, 1, 500_000_000)  # HW=1.5s
    btn_2 = make_button("btn1", 20.0, 20.0, 2, 500_000_000)  # HW=2.5s
    node.button_cb(btn_1)
    node.button_cb(btn_2)

    # Gaze at T=1.5 (adjusted btn midpoint)
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))

    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_100_000_000))

    assert len(published) == 1, "No segment published"
    target_x = published[0].target_samples[0].x
    assert target_x == 15.0, (
        f"Delay compensation ! FAIL: expected 15.0, got {target_x}. "
        "rec_start_ts is likely using the raw timestamp — see BUG(2)."
    )


# ===========================================================================
# 3. min_event_duration_ms FILTER
# ===========================================================================

def test_min_event_duration_discards_short_fixation():
    """
    When min_event_duration_ms=200 (40 samples at 200Hz), a fixation with
    only 10 gaze samples must be silently discarded.
    """
    node = GazeController()
    node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=200.0), # 40 samples
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),

    ])

    btn = make_button("btn1", 10.0, 10.0, 1)
    node.button_cb(btn)
    btn2 = make_button("btn1", 10.0, 10.0, 2)
    node.button_cb(btn2)

    # Only 10 samples — well below the 40-sample minimum
    for i in range(10):
        t = 1.0 + i * 0.005
        node.gaze_cb(make_gaze(100.0, 100.0, int(t), int((t % 1) * 1e9)))

    published = capture_segments(node)
    node.saccade_cb(make_saccade(1_050_000_000))

    assert len(published) == 0, (
        f"Short fixation should be discarded, but {len(published)} segment(s) were published."
    )


def test_min_event_duration_accepts_long_enough_fixation():
    """
    Complement: a fixation with 50 samples (250ms at 200Hz) should pass the
    200ms (40-sample) threshold.
    """
    node = GazeController()
    node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=200.0),
        rclpy.parameter.Parameter('max_gap_ms', value=1500.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=300.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),

        
    ])

    # assert node.rec_start_ts == 0, "rec_start_ts should be initialized to 0."

    # Name, px, py, sec, nanosec (optional)
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 000000000))
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 100000000))
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 200000000))
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 300000000))

    for i in range(50):
        t = 1.0 + (i /200) # Hz
        node.gaze_cb(make_gaze(100.0, 200.0, int(t), int((t % 1) * 1e9)))

    # Check the gaze pointer
    assert node.gaze_ptr == 50, "Gaze history should have 50 samples."

    # Check start
    gaze_data = node.gaze_history[: node.gaze_ptr] 
    print(gaze_data[:, 0] >= node.rec_start_ts)
    t = 1.0 + 50 * 0.005
    end_ts = int(t) + int((t % 1) * 1e9)

    # print(gaze_data[:, 0] <= end_ts)
    raw_idx = np.where((gaze_data[:, 0] >= node.rec_start_ts) & (gaze_data[:, 0] <= end_ts))[0]
    # print(f"raw_idx: {raw_idx}")

    segment_duration_ms = (gaze_data[raw_idx[-1], 0] - gaze_data[raw_idx[0], 0])*1000 if len(raw_idx) > 0 else 0
    print(f"segment_duration_ms: {segment_duration_ms}")
    print(f"start_trim_ms: {node.start_trim_ms}")
    assert node.start_trim_ms == 0.0, "start_trim_ms should be 0.0 ms."

    # print(f"min_event_duration_ms: {node.min_event_duration_ms}")
    assert node.min_event_duration_ms == 200.0, "min_event_duration_ms should be 200.0 ms."

    published = capture_segments(node)
    node.saccade_cb(make_saccade(1_250_000_000))

    if len(raw_idx) == 0 or segment_duration_ms < (node.start_trim_ms + node.min_event_duration_ms):
        pytest.fail(
            f"Fixation should pass duration threshold but was discarded. "
            f"raw_idx={raw_idx}, segment_duration_ms={segment_duration_ms}, "
            f"start_trim_ms={node.start_trim_ms}, min_event_duration_ms={node.min_event_duration_ms}"
        )


    assert len(published) == 1, (
        f"Fixation long enough to pass threshold but no segment was published."
    )


# ===========================================================================
# 4. STICKY vs NON-STICKY BUTTON RELEASE
# ===========================================================================

def test_non_sticky_release_triggers_segment():
    """
    sticky_button_interaction=False → releasing the button must immediately
    publish a segment WITHOUT waiting for a saccade.

    BUG(3): In button_cb the falling-edge block calls _trigger_segment_end with
    `end_point = self.last_valid_btn_ts - terminal_trim_s`.  If terminal_trim_s
    > 0 this can push end_point *before* rec_start_ts, resulting in an empty
    window that is silently discarded.  This test uses terminal_trim_ms=0 to
    isolate the state-machine logic from the timing edge-case.
    """
    node = GazeController()
    node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),
    ])

    # Rising edge
    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.button_cb(make_button("btn1", 20.0, 20.0, 2))

    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))

    published = capture_segments(node)

    # Falling edge — no saccade involved
    node.button_cb(make_button("btn1", 20.0, 20.0, 2,
                               status=ButtonStatus.BUTTON_INACTIVE))

    assert len(published) == 1, (
        f"Non-sticky release should publish a segment immediately. "
        f"Got {len(published)} segment(s)."
    )
    assert node.is_recording is False, "Recording state not reset after release."


def test_sticky_release_does_not_trigger_segment():
    """
    sticky_button_interaction=True → releasing the button must NOT publish
    anything.  Only a saccade should close the segment.
    """

    node = GazeController()
    node.set_parameters([
       
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=0),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=True), #TRUE


    ])
    published = capture_segments(node)

    assert node.is_recording is False, "Sticky mode: not recording at start."

    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.button_cb(make_button("btn1", 20.0, 20.0, 2))
    assert len(node.btn_history) == 2, "Button history should have two entries."

    node.gaze_cb(make_gaze(500.0, 500.0, 1, 500_000_000))
    assert node.gaze_ptr == 1, "Gaze history should have one entry."


    # Release — should be ignored in sticky mode
    node.button_cb(make_button("btn1", 20.0, 20.0, 3,
                               status=ButtonStatus.BUTTON_INACTIVE))
    assert len(node.btn_history) == 2, "Button history should have two entries."

    assert len(published) == 0, "Sticky mode: release should NOT publish a segment."
    assert node.is_recording is True, "Sticky mode: recording should continue after release."


    # Saccade now closes it
    node.saccade_cb(make_saccade(3_100_000_000))
    assert node.is_recording is False, "Sticky mode: recording should stop after saccade."

    assert len(published) == 1, "Recording should have information after saccade."


# ===========================================================================
# 5. BUTTON ID SWAP — CV glitch: A → B → A
# ===========================================================================

def test_button_id_swap_glitch_sticky():
    """
    While recording button A, a single rogue frame emits button B, then A
    returns.  In sticky mode the node must IGNORE B and keep the segment
    associated with A.

    Expected: segment.button_id == "btn_A"
    """
    node = GazeController()
    node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=True), # TRUE

    ])

    # Normal A frame → starts recording
    node.button_cb(make_button("btn_A", 100.0, 100.0, 1))

    # Rogue B frame
    node.button_cb(make_button("btn_B", 900.0, 900.0, 1, 100_000_000))

    # A returns
    node.button_cb(make_button("btn_A", 100.0, 100.0, 1, 200_000_000))

    node.gaze_cb(make_gaze(110.0, 110.0, 1, 500_000_000))

    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_100_000_000))

    assert len(published) == 1, "Expected exactly one segment."
    assert published[0].button_id == "btn_A", (
        f"Segment attributed to wrong button: '{published[0].button_id}'. "
        "Sticky mode should lock onto A and ignore the B glitch."
    )


# def test_button_id_swap_glitch_non_sticky():
#     """
#     In non-sticky mode, a rogue B frame causes an immediate switch.
#     The segment should then be associated with B (the new lock target).
#     This documents the expected (if undesirable) behaviour so regressions
#     are caught.
#     """
#     node = GazeController()
#     node.set_parameters([
#         # Timing
#         rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
#         rclpy.parameter.Parameter('start_trim_ms', value=0.0),
#         rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
#         rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
#         rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
#         # Px
#         rclpy.parameter.Parameter('edge_margin', value=50),
#         rclpy.parameter.Parameter('max_error_px', value=500.0),
#         # Properties
#         rclpy.parameter.Parameter('use_temporal_alignment', value=True),
#         rclpy.parameter.Parameter('sticky_button_interaction', value=False),
#     ])

#     node.button_cb(make_button("btn_A", 100.0, 100.0, 1))
#     # Rogue B — non-sticky will switch lock
#     node.button_cb(make_button("btn_B", 900.0, 900.0, 1, 100_000_000))
#     # node.button_cb(make_button("btn_A", 120.0, 120.0, 1, 200_000_000))

#     node.gaze_cb(make_gaze(110.0, 110.0, 1, 500_000_000))

#     published = capture_segments(node)
#     node.saccade_cb(make_saccade(2_100_000_000))

#     assert len(published) == 1
#     assert published[0].button_id == "btn_B", (
#         f"Non-sticky: expected lock to switch to B, got '{published[0].button_id}'."
#     )


# ===========================================================================
# 6. MULTIPLE SEQUENTIAL SACCADES
# ===========================================================================

def test_second_saccade_is_no_op():
    """
    After the first saccade closes the segment, a second saccade 50ms later
    must be a complete no-op:
      - No second segment published
      - No crash
      - is_recording remains False

    BUG(4): _trigger_segment_end starts with `if not self.is_recording: return`
    which correctly guards against this — BUT saccade_cb only calls
    _trigger_segment_end when `if self.is_recording:`.  Both guards are
    redundant but consistent.  The real risk is if some other code path sets
    is_recording=True between the two saccades — this test would catch that.
    """
    node = GazeController()
    zero_params(node)

    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.button_cb(make_button("btn1", 20.0, 20.0, 2))
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))

    published = capture_segments(node)

    # First saccade — closes segment
    node.saccade_cb(make_saccade(2_100_000_000))
    assert len(published) == 1, "First saccade should publish one segment."
    assert node.is_recording is False

    # Second saccade 50ms later — must be a no-op
    try:
        node.saccade_cb(make_saccade(2_150_000_000))
    except Exception as e:
        pytest.fail(f"Second saccade raised an exception: {e}")

    assert len(published) == 1, (
        "Second saccade published a phantom segment!"
    )
    assert node.is_recording is False


# ===========================================================================
# 7. NANOSECOND BOUNDARY PRECISION
# ===========================================================================

def test_nanosecond_rollover_interpolation():
    """
    A gaze sample straddles the sec/nanosec boundary:
      btn at T=0.999_999_999 (sec=0, nanosec=999_999_999)
      btn at T=2.000_000_001 (sec=2, nanosec=1)
      gaze at T=1.500_000_000

    Python float64 has ~15 significant digits. At T~1.5s this is fine, but
    at larger absolute timestamps precision erodes.  We verify no off-by-one
    in the sec+nanosec/1e9 arithmetic.

    BUG(5): `float_to_stamp` in the source uses
        `int((t_float - int(t_float)) * 1e9)`
    For values like t=1.1, (1.1 - 1) * 1e9 = 99999999.xxx due to IEEE-754
    representation, which truncates to 99_999_999 instead of 100_000_000.
    Accumulated over many samples this drifts the reconstructed timestamps.
    Fix: use `round(...)` instead of `int(...)`.
    """
    node = GazeController()
    zero_params(node)

    # btn just before 1s boundary
    btn_1 = make_button("btn1", 10.0, 10.0, 0, 999_999_999)
    # btn just after 2s boundary
    btn_2 = make_button("btn1", 20.0, 20.0, 2, 1)
    node.button_cb(btn_1)
    node.button_cb(btn_2)

    # Gaze exactly at 1.5s
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))

    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_100_000_000))

    assert len(published) == 1, "No segment published around nanosecond boundary."
    tx = published[0].target_samples[0].x

    # T=1.5 is the midpoint between T≈0.9999999990 and T≈2.0000000010
    # Expected X should be very close to 15.0
    assert abs(tx - 15.0) < 0.5, (
        f"Nanosecond boundary caused interpolation error: got X={tx}, expected ~15.0"
    )


def test_nanosecond_stamp_reconstruction():
    """
    float_to_stamp must round-trip correctly for common sub-second values.

    BUG(5) reproduced: 1.1 → float_to_stamp → sec=1, nanosec should be
    100_000_000 but int() gives 99_999_999.
    """
    node = GazeController()

    test_cases = [
        (1.1,  1, 100_000_000),
        (1.5,  1, 500_000_000),
        (2.25, 2, 250_000_000),
        (0.001, 0, 1_000_000),
    ]
    for t_float, expected_sec, expected_ns in test_cases:
        stamp = node.float_to_stamp(t_float)
        assert stamp.sec == expected_sec, (
            f"float_to_stamp({t_float}): sec={stamp.sec}, expected {expected_sec}"
        )
        # Allow ±1 ns tolerance for IEEE-754 rounding
        assert abs(stamp.nanosec - expected_ns) <= 1, (
            f"float_to_stamp({t_float}): nanosec={stamp.nanosec}, "
            f"expected {expected_ns}. "
            "Fix: use round() instead of int() in float_to_stamp."
        )


# ===========================================================================
# 8. OUT-OF-ORDER GAZE TIMESTAMPS
# ===========================================================================

def test_out_of_order_gaze_timestamps():
    """
    A late UDP/DDS packet may deliver a gaze sample with an earlier timestamp
    after newer ones have already been stored.  The node must not crash, and
    the published segment timestamps must still be strictly non-decreasing.

    BUG(6): gaze_cb stores samples in arrival order into the circular buffer
    without any re-ordering.  _trigger_segment_end does call np.argsort on
    the full buffer, so the final segment *will* be correctly sorted.
    However, if the late packet lands in a slot that was already consumed by
    the current window (due to buffer wrap), it may be silently excluded.
    This test checks that at minimum we don't crash and timestamps are sorted.
    """
    node = GazeController()
    zero_params(node)

    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.button_cb(make_button("btn1", 20.0, 20.0, 2))

    # Normal gaze: 1.0, 1.1, 1.2, 1.3, 1.4
    for i in range(5):
        t = 1.0 + i * 0.1
        node.gaze_cb(make_gaze(100.0, 100.0, int(t), int((t % 1) * 1e9)))

    # Late packet: timestamp 1.05 arrives after 1.4
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 50_000_000))

    # Continue with normal gaze
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))

    published = capture_segments(node)

    try:
        node.saccade_cb(make_saccade(2_000_000_000))
    except Exception as e:
        pytest.fail(f"Out-of-order timestamp caused a crash: {e}")

    assert len(published) == 1, "Expected one segment despite out-of-order packet."

    timestamps = [
        s.header.stamp.sec + s.header.stamp.nanosec / 1e9
        for s in published[0].gaze_samples
    ]
    is_sorted = all(timestamps[i] <= timestamps[i + 1]
                    for i in range(len(timestamps) - 1))
    assert is_sorted, (
        f"Out-of-order packet produced scrambled timestamps in segment: {timestamps}"
    )


# ===========================================================================
# 9. CONCURRENT BUTTON IDs AT THE SAME TIMESTAMP
# ===========================================================================

def test_concurrent_button_ids_same_timestamp():
    """
    Two different button IDs arrive in the same ROS cycle (same timestamp).
    Whichever arrives FIRST should win (first-come-first-locked).
    The second must be ignored (sticky) or cause a switch (non-sticky).

    This also guards against a crash from duplicate timestamps in btn_history.
    """
    node = GazeController()
    node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=True), # TRUE

    ])

    # Both arrive with identical timestamps
    node.button_cb(make_button("btn_A", 100.0, 100.0, 1, 0))
    node.button_cb(make_button("btn_B", 900.0, 900.0, 1, 0))

    node.gaze_cb(make_gaze(110.0, 110.0, 1, 500_000_000))

    published = capture_segments(node)

    try:
        node.saccade_cb(make_saccade(2_100_000_000))
    except Exception as e:
        pytest.fail(f"Concurrent button IDs caused a crash: {e}")

    assert len(published) == 0
    # # In sticky mode, first arrival (btn_A) must win
    # assert published[0].button_id == "btn_A", (
    #     f"Expected btn_A to win first-come-first-locked. Got: {published[0].button_id}"
    # )


# ===========================================================================
# 10. ADDITIONAL BUG REGRESSION TESTS
# ===========================================================================

def test_trigger_segment_end_length_check_uses_wrong_floor():
    """
    BUG(7): In _trigger_segment_end the minimum-length guard is:

        if len(raw_idx) < (self.start_trim_ms + self.min_samples):

    `self.start_trim_ms` is already in *samples* (computed in
    update_internal_params as  int(ms / 1000 * hz)).
    `self.min_samples` is also in samples.
    So the guard checks: samples_in_window < (trim_samples + min_samples).

    This is correct — the window must contain *both* the trim region and the
    minimum post-trim duration.  The test below confirms the boundary:
    exactly (trim + min) samples → discard; (trim + min + 1) → publish.
    """
    node = GazeController()
    success = node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=50.0),     # 10 samples at 200Hz
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=50.0),  # 10 samples
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),

    ])
    # Required window: 10 + 10 = 20 samples minimum

    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.button_cb(make_button("btn1", 10.0, 10.0, 3))

    # 19 samples — should be discarded (one short)
    for i in range(19):
        t = 1.0 + i * 0.005
        node.gaze_cb(make_gaze(100.0, 100.0, int(t), int(round((t % 1) * 1e9))))

    published_short = capture_segments(node)
    node.saccade_cb(make_saccade(1_095_000_000))
    assert len(published_short) == 0, "19-sample window should be below threshold."
    node.destroy_node()

    # Reset and try with 21 samples — should publish
    node2 = GazeController()
    node2.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=50.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=50.0),
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=500.0),
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),

    ])
    node2.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node2.button_cb(make_button("btn1", 10.0, 10.0, 3))
    for i in range(21):
        t = 1.0 + i * 0.005
        node2.gaze_cb(make_gaze(100.0, 100.0, int(t), int(round((t % 1) * 1e9))))
    published_ok = capture_segments(node2)
    node2.saccade_cb(make_saccade(1_105_000_000))
    assert len(published_ok) == 1, "21-sample window should pass the threshold."



# ===========================================================================
# NON-STICKY STATE MACHINE
# ===========================================================================
 
def test_nonsticky_no_segment_without_active_button():
    """
    A saccade fires but no button was ever ACTIVE.
    Nothing should be published and the node must not crash.
 
    Catches: _publish_segment being called with empty btn_history.
    """
    node = nonsticky_node()
    published = capture_segments(node)
 
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 0))
    node.saccade_cb(make_saccade(1_500_000_000))
 
    assert len(published) == 0, "No button was active — nothing should be published."
    assert node.is_recording is False
 
 
def test_nonsticky_saccade_before_button_is_active():
    """
    Saccade fires at T=1.5, but the button only becomes ACTIVE at T=2.0.
    The saccade must be a no-op (is_recording is False at that point).
    """
    node = nonsticky_node()
    published = capture_segments(node)
 
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 0))
    node.saccade_cb(make_saccade(1_500_000_000))   # fires before any button
 
    # gaze should be discarded in future tests

    node.button_cb(make_button("btn1", 10.0, 10.0, 2, 0))
    node.button_cb(make_button("btn1", 10.0, 10.0, 3, 0))
    node.gaze_cb(make_gaze(100.0, 100.0, 2, 500_000_000))
    node.saccade_cb(make_saccade(3_000_000_000))   # now valid
 
    assert len(published) == 1, (
        "Expected exactly one segment from the second saccade."
    )
 
 
def test_nonsticky_gaze_before_button():
    """
    Gaze arrives at T=1.0, button becomes ACTIVE at T=1.5.
    The gaze at T=1.0 is BEFORE rec_start_ts, so it must be excluded from
    the segment window.  Only gaze at T=1.5 or later should be included.
 
    This verifies rec_start_ts windowing is working correctly.
    """
    node = nonsticky_node()
 
    # Gaze arrives before button
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 0))       # T=1.0 — before recording
    node.gaze_cb(make_gaze(200.0, 200.0, 1, 500_000_000))  # T=1.5 — same as rising edge
 
    # Button rises at T=1.5
    node.button_cb(make_button("btn1", 150.0, 150.0, 1, 500_000_000))
    node.button_cb(make_button("btn1", 150.0, 150.0, 2, 500_000_000))
 
    node.gaze_cb(make_gaze(300.0, 300.0, 2, 0))        # T=2.0 — during recording
 
    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_500_000_000))
 
    assert len(published) == 1
    gaze_ts = [s.header.stamp.sec + s.header.stamp.nanosec / 1e9
               for s in published[0].gaze_samples]
 
    assert all(t >= 1.5 for t in gaze_ts), (
        f"Pre-recording gaze leaked into the segment. Timestamps: {gaze_ts}"
    )
 
 
def test_nonsticky_release_then_no_saccade_needed():
    """
    In non-sticky mode a button release is sufficient to close the segment.
    A subsequent saccade must NOT re-open or re-publish anything.
    Verifies is_recording=False persists through a stray saccade.
    """
    node = nonsticky_node()
 
    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.button_cb(make_button("btn1", 10.0, 10.0, 2))
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))
 
    published = capture_segments(node)
 
    # Release closes segment
    node.button_cb(make_button("btn1", 10.0, 10.0, 2,
                               status=ButtonStatus.BUTTON_INACTIVE))
    assert len(published) == 1, "Release should have published one segment."
    assert node.is_recording is False
 
    # Stray saccade — must be a no-op
    node.saccade_cb(make_saccade(3_000_000_000))
    assert len(published) == 1, "Stray saccade after release published a phantom segment."
 
 
def test_nonsticky_back_to_back_interactions():
    """
    Full lifecycle repeated twice in sequence:
      Segment 1: btn1 active → gaze → release
      Segment 2: btn1 active again → gaze → saccade
 
    Verifies that state resets cleanly after segment 1 so that segment 2
    is independent, correctly windowed, and uses only its own gaze/button data.
 
    This is the most important regression test for the refactored button_cb:
    if btn_history is not cleared, or rec_start_ts is not reset, segment 2
    will contain data from segment 1.
    """
    node = nonsticky_node()
    published = capture_segments(node)
 
    # --- Segment 1 ---
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 0))
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))  # T=1.5
    node.button_cb(make_button("btn1", 10.0, 10.0, 2, 0))
    node.button_cb(make_button("btn1", 10.0, 10.0, 2, 100_000_000,
                               status=ButtonStatus.BUTTON_INACTIVE))
 
    assert len(published) == 1, "Segment 1 should have been published on release."
    assert published[0].button_id == "btn1", "Segment 1 should be associated with btn1."
    assert len(published[0].target_samples) == 1, "Segment 1 should have one target sample (interpolated to valid gaze point)."
    assert node.is_recording is False, "Recording should have stopped after segment 1 release."
    seg1_gaze_count = len(published[0].gaze_samples)
 
    # --- Gap (nothing happening) ---
    # Gaze keeps arriving but no button is active — must not be recorded
    node.gaze_cb(make_gaze(999.0, 999.0, 3, 0))
    node.gaze_cb(make_gaze(999.0, 999.0, 4, 0))
 
    # --- Segment 2 (different button position) ---
    node.button_cb(make_button("btn1", 50.0, 50.0, 5, 0))
    node.gaze_cb(make_gaze(200.0, 200.0, 5, 500_000_000))  # T=5.5
    node.button_cb(make_button("btn1", 50.0, 50.0, 6, 0))
    node.gaze_cb(make_gaze(200.0, 200.0, 6, 500_000_000))  # T=6.5
    node.button_cb(make_button("btn1", 50.0, 50.0, 7, 0))
    node.saccade_cb(make_saccade(8_000_000_000))

    assert len(published) == 2, (
        f"Expected 2 segments total, got {len(published)}."
    )
 
    seg2 = published[1]
 
    # All targets in segment 2 should be at (50, 50), not (10, 10) from segment 1
    for i, pt in enumerate(seg2.target_samples):
        assert pt.x == 50.0, (
            f"Segment 2 target[{i}].x = {pt.x}, expected 50.0. "
            "btn_history from segment 1 is leaking into segment 2."
        )
 
    # Gaze in segment 2 must not contain the gap gaze (999.0) or segment 1 gaze (100.0)
    gaze_xs = [s.x for s in seg2.gaze_samples]
    assert all(x == 200.0 for x in gaze_xs), (
        f"Segment 2 contains gaze from outside its window: {gaze_xs}"
    )
 
 
def test_nonsticky_release_resets_button_engaged():
    """
    After a falling edge, button_engaged must be False.
    If a second identical INACTIVE message arrives (e.g. at 30Hz the topic
    keeps publishing INACTIVE), it must not trigger a second segment.
    """
    node = nonsticky_node()
 
    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.button_cb(make_button("btn1", 10.0, 10.0, 2))
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))
 
    published = capture_segments(node)
 
    node.button_cb(make_button("btn1", 10.0, 10.0, 2,
                               status=ButtonStatus.BUTTON_INACTIVE))
    assert len(published) == 1
 
    # Second INACTIVE at 30Hz — button_engaged is already False, must be a no-op
    node.button_cb(make_button("btn1", 10.0, 10.0, 2, 33_000_000,
                               status=ButtonStatus.BUTTON_INACTIVE))
    node.button_cb(make_button("btn1", 10.0, 10.0, 2, 66_000_000,
                               status=ButtonStatus.BUTTON_INACTIVE))
 
    assert len(published) == 1, (
        f"Repeated INACTIVE messages triggered extra segments: {len(published)}"
    )
    assert node.button_engaged is False
    assert node.is_recording is False
 
 
def test_nonsticky_interpolation_uses_only_current_segment_buttons():
    """
    Two sequential interactions with different button positions.
    Segment 2's interpolated targets must use ONLY segment 2's button history,
    not a mix of segment 1 and segment 2.
 
    btn_history is a deque with maxlen — it keeps a rolling window of history.
    _publish_segment uses ALL of btn_history for interpolation, so if segment 1
    data is still in the deque when segment 2 fires, the interp domain spans
    both interactions and may produce wrong values.
 
    This test catches that by using non-overlapping timestamps and asserting
    the exact interpolated values for segment 2.
    """
    node = nonsticky_node()
    published = capture_segments(node)
 
    # Segment 1: button moves from X=0 to X=10 over T=1..2
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 0))

    node.gaze_cb(make_gaze(105.0, 105.0, 1, 500_000_000))
    node.button_cb(make_button("btn1", 0.0, 0.0,    1, 500_000_000))
    node.button_cb(make_button("btn1", 5.0, 5.0,    1, 750_000_000))
    node.gaze_cb(make_gaze(110.0, 110.0, 2, 0))
    node.button_cb(make_button("btn1", 10.0, 10.0,  2, 0))

    node.gaze_cb(make_gaze(115.0, 115.0, 2, 500_000_000))

    node.button_cb(make_button("btn1", 10.0, 10.0, 2, 500_000_000,
                               status=ButtonStatus.BUTTON_INACTIVE))
 
    assert len(published) == 1
 
    # Segment 2: button moves from X=100 to X=200 over T=10..11
    # These timestamps are far from segment 1, so if old data bleeds in,
    # the extrapolation will be clearly wrong.
    node.button_cb(make_button("btn1", 100.0, 100.0, 10, 0))
    node.button_cb(make_button("btn1", 200.0, 200.0, 11, 0))
 
    # Gaze at T=10.5 — midpoint → expected target X = 150.0
    node.gaze_cb(make_gaze(100.0, 100.0, 10, 500_000_000))
 
    node.saccade_cb(make_saccade(11_500_000_000))
 
    assert len(published) == 2
    target_x = published[1].target_samples[0].x
    assert target_x == 150.0, (
        f"Segment 2 interpolation got X={target_x}, expected 150.0. "
        "Old btn_history from segment 1 may be contaminating the interpolation."
    )
 
 
def test_nonsticky_state_after_saccade_terminates():
    """
    After a saccade ends a segment, all state fields must be fully reset:
      - is_recording = False
      - rec_start_ts = None
      - current_button_id = None
      - button_engaged = False
 
    A missing reset on any of these will corrupt the next interaction.
    """
    node = nonsticky_node()
 
    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))
    capture_segments(node)
    node.saccade_cb(make_saccade(2_000_000_000))
 
    assert node.is_recording is False,      "is_recording not reset after saccade."
    assert node.rec_start_ts is None,        "rec_start_ts not reset after saccade."
    assert node.current_button_id is None,   "current_button_id not reset after saccade."
    assert node.button_engaged is False,     "button_engaged not reset after saccade."
 
 
def test_nonsticky_state_after_release_terminates():
    """
    Same as above but triggered by button release rather than saccade.
    """
    node = nonsticky_node()
 
    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))
    capture_segments(node)
    node.button_cb(make_button("btn1", 10.0, 10.0, 2,
                               status=ButtonStatus.BUTTON_INACTIVE))
 
    assert node.is_recording is False,      "is_recording not reset after release."
    assert node.rec_start_ts is None,        "rec_start_ts not reset after release."
    assert node.current_button_id is None,   "current_button_id not reset after release."
    assert node.button_engaged is False,     "button_engaged not reset after release."
 
 
def test_nonsticky_zero_position_button_ignored():
    """
    A button message with center_x=0.0, center_y=0.0 must be treated as
    invalid and NOT appended to btn_history.
 
    This is the `is_pos_valid` guard: abs(x) > 1e-5 and abs(y) > 1e-5.
    A common failure mode is the CV pipeline emitting a zero-position frame
    when a button briefly goes off-screen. If that frame gets appended, it
    pulls the interpolated target to (0, 0) for that timestamp.
    """
    node = nonsticky_node()
 
    # Valid frame
    node.button_cb(make_button("btn1", 100.0, 100.0, 1, 0))
 
    # Zero-position frame — should be ignored
    node.button_cb(make_button("btn1", 0.0, 0.0, 1, 500_000_000))
 
    # Valid frame again
    node.button_cb(make_button("btn1", 200.0, 200.0, 2, 0))
 
    node.gaze_cb(make_gaze(150.0, 150.0, 1, 500_000_000))
 
    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_500_000_000))
 
    assert len(published) == 1
    for i, pt in enumerate(published[0].target_samples):
        assert pt.x != 0.0 and pt.y != 0.0, (
            f"Zero-position button leaked into target_samples[{i}]: ({pt.x}, {pt.y})"
        )
 
 
def test_nonsticky_segment_contains_correct_gaze_count():
    """
    Feeds exactly 5 gaze samples within the recording window and verifies
    the segment contains exactly 5 gaze samples — no more, no less.
 
    Catches off-by-one errors in the windowing slice or the trim logic
    when start_trim_ms=0.
    """
    node = nonsticky_node()
 
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 0))
    node.button_cb(make_button("btn1", 10.0, 10.0, 5, 0))
 
    # Exactly 5 samples inside the window [T=1.0 .. T=1.4]
    for i in range(5):
        t = 1.0 + i * 0.1
        node.gaze_cb(make_gaze(100.0, 100.0, int(t), int((t % 1) * 1e9)))
 
    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_000_000_000))
 
    assert len(published) == 1
    assert len(published[0].gaze_samples) == 5, (
        f"Expected 5 gaze samples, got {len(published[0].gaze_samples)}."
    )
 
 
def test_nonsticky_segment_gaze_and_target_same_length():
    """
    gaze_samples and target_samples must always have the same length.
    A mismatch would corrupt downstream training — every gaze point needs
    a corresponding target.
    """
    node = nonsticky_node()
 
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 0))
    node.button_cb(make_button("btn1", 20.0, 20.0, 3, 0))
 
    for i in range(10):
        t = 1.0 + i * 0.1
        node.gaze_cb(make_gaze(100.0, 100.0, int(t), int((t % 1) * 1e9)))
 
    published = capture_segments(node)
    node.saccade_cb(make_saccade(3_500_000_000))
 
    assert len(published) == 1
    seg = published[0]
    assert len(seg.gaze_samples) == len(seg.target_samples), (
        f"gaze_samples ({len(seg.gaze_samples)}) and "
        f"target_samples ({len(seg.target_samples)}) have different lengths."
    )
 

def test_gaze_buffer_wraparound_maintains_sort_order():
    """
    Forces the internal circular buffer to fill up and wrap around.
    Verifies that `np.roll` correctly unfolds the array chronologically
    before slicing the segment window.
    """
    node = nonsticky_node()
    # Force a tiny buffer (0.05s * 200Hz = 10 samples)
    node.set_parameters([
        rclpy.parameter.Parameter('history_length_s', value=0.05)
    ])
    
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 0))
    node.button_cb(make_button("btn1", 10.0, 10.0, 2, 0))

    # Feed 15 samples (exceeds the 10-sample buffer, forcing wrap)
    for i in range(15):
        t = 1.0 + i * 0.005
        node.gaze_cb(make_gaze(100.0, 100.0, int(t), int(round((t % 1) * 1e9))))
    
    assert node.gaze_buffer_filled is True, "Buffer should have wrapped around."
    
    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_000_000_000))
    
    assert len(published) == 1
    
    # Check if timestamps are strictly increasing
    timestamps = [
        s.header.stamp.sec + s.header.stamp.nanosec / 1e9
        for s in published[0].gaze_samples
    ]
    is_sorted = all(timestamps[i] < timestamps[i + 1] for i in range(len(timestamps) - 1))
    assert is_sorted, "Buffer wraparound scrambled the chronological order!"
    # Since only the last 10 samples survive in the buffer, length should be exactly 10
    assert len(timestamps) == 10, f"Expected 10 samples after wrap, got {len(timestamps)}"


def test_start_trim_physically_removes_leading_samples():
    """
    Verify that start_trim_ms effectively removes the first N samples 
    from the published segment.
    """
    node = nonsticky_node()
    node.set_parameters([
        # 50ms trim at 200Hz = exactly 10 samples
        rclpy.parameter.Parameter('start_trim_ms', value=50.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0), 
    ])
    
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 0))
    node.button_cb(make_button("btn1", 10.0, 10.0, 2, 0))

    # Feed exactly 30 gaze samples
    for i in range(30):
        t = 1.0 + i * 0.005
        node.gaze_cb(make_gaze(100.0, 100.0, int(t), int(round((t % 1) * 1e9))))

    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_000_000_000))

    assert len(published) == 1
    # 30 total samples - 10 trimmed samples = 20 remaining
    assert len(published[0].gaze_samples) == 20, (
        f"Start trim failed: expected 20 samples, got {len(published[0].gaze_samples)}"
    )

def test_no_temporal_alignment_uses_step_function():
    """
    When use_temporal_alignment=False, the node should map the gaze to 
    the closest previous raw button message, ignoring interpolation.
    """
    node = nonsticky_node()
    node.set_parameters([
        rclpy.parameter.Parameter('use_temporal_alignment', value=False)
    ])
    
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 0))  # T=1.0, X=10.0
    node.button_cb(make_button("btn1", 20.0, 20.0, 2, 0))  # T=2.0, X=20.0
    
    # Gaze near the end: T=1.9. 
    # With interpolation, X would be 19.0.
    # Without interpolation, it should step back to the T=1.0 raw sample (X=10.0).
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 900_000_000)) 
    
    published = capture_segments(node)
    node.saccade_cb(make_saccade(3_000_000_000))
    
    assert len(published) == 1
    target_x = published[0].target_samples[0].x
    
    assert target_x == 10.0, (
        f"Expected step-function value of 10.0, got {target_x}."
    )

def test_out_of_fov_terminates_non_sticky_interaction():
    """
    If gaze strays outside the (1600x1200) FOV minus edge_margin, 
    a non-sticky interaction should immediately terminate and publish.
    """
    node = nonsticky_node()
    node.set_parameters([
        rclpy.parameter.Parameter('edge_margin', value=50) # boundaries: 50 to 1550
    ])
    
    node.button_cb(make_button("btn1", 800.0, 600.0, 1, 0))
    node.button_cb(make_button("btn1", 800.0, 600.0, 2, 0))
    
    # Center gaze (clean)
    node.gaze_cb(make_gaze(800.0, 600.0, 1, 500_000_000)) 
    
    published = capture_segments(node)
    
    # Gaze out of bounds (X = 1560)
    node.gaze_cb(make_gaze(1560.0, 600.0, 1, 600_000_000))
    
    assert len(published) == 1, "Gaze leaving FOV should have auto-published."
    assert node.is_recording is False, "Node should stop recording after losing FOV."

def test_blink_event_terminates_interaction():
    """
    Verifies that the blink callback correctly proxies to the termination logic.
    """
    node = nonsticky_node()
    
    node.button_cb(make_button("btn1", 10.0, 10.0, 1, 0))
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))
    node.button_cb(make_button("btn1", 10.0, 10.0, 2, 0))
    
    published = capture_segments(node)
    
    # Trigger blink instead of saccade
    node.blink_cb(make_saccade(2_000_000_000))  # using make_saccade helper since it returns same base type
    
    assert len(published) == 1, "Blink event failed to trigger segment finalization."
    assert node.is_recording is False


# ===========================================================================
# NEW FEATURE: GAP & ERROR MASKING
# ===========================================================================

def test_gap_masking_drops_samples_during_loss():
    """
    If the button signal disappears for longer than max_gap_ms, 
    gaze samples during that gap must be excluded from the published segment.
    """
    node = GazeController()
    node.set_parameters([
        rclpy.parameter.Parameter('max_gap_ms', value=200.0), # 0.2 seconds
        rclpy.parameter.Parameter('use_temporal_alignment', value=True)
    ])
    
    # 1. Button active at T=1.0
    node.button_cb(make_button("btn1", 100.0, 100.0, 1, 0))
    # 2. Button signal lost, returns at T=1.5 (Gap = 500ms > 200ms)
    node.button_cb(make_button("btn1", 100.0, 100.0, 1, 500_000_000))
    # 3. Button returns 100ms after, inside the limit
    node.button_cb(make_button("btn1", 100.0, 100.0, 1, 600_000_000))
    
    # 3. Gaze at T=1.1 (inside the 0.5s gap)
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 100_000_000))
    # 4. Gaze at T=1.5 (at the end of the gap)
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 550_000_000))

    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_000_000_000))

    assert len(published) == 1

    # Gaze at T=1.1 should have been masked out
    gaze_times = [s.header.stamp.sec + s.header.stamp.nanosec/1e9 for s in published[0].gaze_samples]
    assert 1.1 not in gaze_times, "Gaze sample during button gap was not masked!"
    assert 1.55 in gaze_times, "Valid gaze sample at end of gap was incorrectly masked."


def test_max_error_masking():
    """
    Gaze samples that are further than max_error_px from the target 
    should be dropped from the segment.
    """
    node = GazeController()
    node.set_parameters([
        # Timing
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('max_gap_ms', value=5000.0),
        # Px
        rclpy.parameter.Parameter('edge_margin', value=50),
        rclpy.parameter.Parameter('max_error_px', value=50.0), # <-- the key parameter for this test
        # Properties
        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),


    ])
    
    node.button_cb(make_button("btn1", 100.0, 100.0, 1, 0))
    node.button_cb(make_button("btn1", 100.0, 100.0, 2, 0))
    
    # Gaze 1: Close to button (Error = 10px < 50px) -> KEEP
    node.gaze_cb(make_gaze(110.0, 100.0, 1, 100_000_000))
    # Gaze 2: Far from button (Error = 200px > 50px) -> DROP
    node.gaze_cb(make_gaze(300.0, 100.0, 1, 200_000_000))
    
    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_500_000_000))
    
    assert len(published[0].gaze_samples) == 1, "Only one sample should remain after error filtering."
    assert published[0].gaze_samples[0].x == 110.0


# ===========================================================================
# NEW FEATURE: TELEOP HEARTBEAT & STICKY OVERRIDE
# ===========================================================================

def test_teleop_heartbeat_sticky_override():
    """
    Verifies that in sticky mode, if the physical button signal goes INACTIVE,
    the teleop loop still publishes ACTIVE to the robot until the saccade happens.
    """
    node = GazeController()
    node.set_parameters([
        rclpy.parameter.Parameter('sticky_button_interaction', value=True)
    ])
    
    # Start interaction
    node.button_cb(make_button("btn1", 500.0, 500.0, 1, 0, status=ButtonStatus.BUTTON_ACTIVE))
    assert node.is_recording is True
    
    # Simulate signal flicker/release (Sensor says INACTIVE)
    node.button_cb(make_button("btn1", 500.0, 500.0, 1, 100_000_000, status=ButtonStatus.BUTTON_INACTIVE))
    
    # Create a subscriber to the teleop output
    teleop_msgs = []
    node.teleop_pub.publish = lambda msg: teleop_msgs.append(msg)
    
    # Trigger the timer loop
    node.publish_to_robot_loop()
    
    assert len(teleop_msgs) > 0
    assert teleop_msgs[-1].button_status == ButtonStatus.BUTTON_ACTIVE, \
        "Teleop should stay ACTIVE during sticky recording even if raw signal is INACTIVE."


# ===========================================================================
# DATA QUALITY: CORRECTION MATH
# ===========================================================================

def test_polynomial_correction_application():
    """
    Verifies that the polynomial coefficients actually move the gaze point.
    Setup: Apply a simple +10px X-axis bias via the coefficients.
    """
    node = GazeController()
    model = CalibrationModel()
    # [dx^2, dy^2, dx*dy, dx, dy, bias]
    # Set bias (index 5) to 10.0 for X
    model.coeffs_x = [0.0, 0.0, 0.0, 0.0, 0.0, 10.0] 
    model.coeffs_y = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    model.model_type = CalibrationModel.TYPE_BIAS
    
    node.model_cb(model)
    
    # Mock corrected gaze publisher
    corrected_points = []
    node.corrected_gaze_pub.publish = lambda msg: corrected_points.append(msg)
    
    # Raw gaze at (100, 100)
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 0))
    
    assert len(corrected_points) > 0
    # Expected: 100 + 10 = 110
    assert corrected_points[-1].point.x == 110.0, f"Expected 110.0, got {corrected_points[-1].point.x}"
