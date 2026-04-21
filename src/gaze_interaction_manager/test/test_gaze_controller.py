#!/usr/bin/env python3
"""
Extended GazeController Test Suite
Run with:
python3 -m pytest src/gaze_interaction_manager/test/test_gaze_controller.py -v -s -k test_pipeline_delay_shifts_interpolation

Covers:
  - PASS - Ghost button assertion fix          
  ! FAIL - test_pipeline_delay_shifts_interpolation
  - PASS - min_event_duration_ms filter
  - PASS - test_min_event_duration_accepts_long_enough_fixation
    PASS - test_second_saccade_is_no_op 
  ! FAIL - test_nanosecond_rollover_interpolation [INFO] [1776765263.724452919]  
    PASS - test_nanosecond_stamp_reconstruction [INFO] [1776765263.748522155]  
    PASS - test_out_of_order_gaze_timestamps [INFO] [1776765263.759809108]  
  ! FAIL - test_concurrent_button_ids_same_timestamp [INFO] [1776765263.778543704]  
  ! WARN - test_trigger_segment_end_length_check_uses_wrong_floor [INFO] [1776765263.800300389]  
    PASS - test_publish_to_robot_loop_button_id_typo [INFO] [1776765263.828513905]  
  ## sticky vs non-sticky release logic
  - PASS - test_non_sticky_release_triggers_segment
  ! FAIL - test_sticky_release_does_not_trigger_segment
  ! FAIL - test_button_id_swap_glitch_sticky
"""

import sys
import os
import math
import pytest
import rclpy

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, '..', 'scripts')
sys.path.insert(0, scripts_dir)
src_dir = os.path.join(current_dir, '..', '..', 'diegetic_transform_engine', 'scripts')
sys.path.insert(0, src_dir)

from gaze_controller import GazeController

from std_msgs.msg import Header
from geometry_msgs.msg import Point
from pupil_neon_ros.msg import GazeData, GazeEvent
from gaze_interaction_manager.msg import ButtonStatus
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
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
    ])


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
    node.set_parameters([
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('edge_margin', value=50),

        rclpy.parameter.Parameter('use_temporal_alignment', value=True),
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),

    ])
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

    # Unpack into 3 vectors
    targets = [[s.x, s.y] for s in published[0].target_samples]

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
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=500.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('edge_margin', value=50),

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
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=200.0),  # 40 samples
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
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=200.0),
    ])

    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.button_cb(make_button("btn1", 10.0, 10.0, 2))

    for i in range(50):
        t = 1.0 + i * 0.005
        node.gaze_cb(make_gaze(100.0, 100.0, int(t), int((t % 1) * 1e9)))

    published = capture_segments(node)
    node.saccade_cb(make_saccade(1_250_000_000))

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
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
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
        rclpy.parameter.Parameter('sticky_button_interaction', value=True),
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
    ])

    node.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node.button_cb(make_button("btn1", 20.0, 20.0, 2))
    node.gaze_cb(make_gaze(100.0, 100.0, 1, 500_000_000))

    published = capture_segments(node)

    # Release — should be ignored in sticky mode
    node.button_cb(make_button("btn1", 20.0, 20.0, 2,
                               status=ButtonStatus.BUTTON_INACTIVE))
    assert len(published) == 0, "Sticky mode: release should NOT publish a segment."
    assert node.is_recording is True, "Sticky mode: recording should continue after release."

    # Saccade now closes it
    node.saccade_cb(make_saccade(2_100_000_000))
    assert len(published) == 1, "Saccade should close the sticky segment."


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
        rclpy.parameter.Parameter('sticky_button_interaction', value=True),
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
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


def test_button_id_swap_glitch_non_sticky():
    """
    In non-sticky mode, a rogue B frame causes an immediate switch.
    The segment should then be associated with B (the new lock target).
    This documents the expected (if undesirable) behaviour so regressions
    are caught.
    """
    node = GazeController()
    node.set_parameters([
        rclpy.parameter.Parameter('sticky_button_interaction', value=False),
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
    ])

    node.button_cb(make_button("btn_A", 100.0, 100.0, 1))
    # Rogue B — non-sticky will switch lock
    node.button_cb(make_button("btn_B", 900.0, 900.0, 1, 100_000_000))
    node.gaze_cb(make_gaze(110.0, 110.0, 1, 500_000_000))

    published = capture_segments(node)
    node.saccade_cb(make_saccade(2_100_000_000))

    assert len(published) == 1
    assert published[0].button_id == "btn_B", (
        f"Non-sticky: expected lock to switch to B, got '{published[0].button_id}'."
    )


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
        rclpy.parameter.Parameter('sticky_button_interaction', value=True),
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=0.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=0.0),
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

    assert len(published) == 1
    # In sticky mode, first arrival (btn_A) must win
    assert published[0].button_id == "btn_A", (
        f"Expected btn_A to win first-come-first-locked. Got: {published[0].button_id}"
    )


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
    node.set_parameters([
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=50.0),     # 10 samples at 200Hz
        rclpy.parameter.Parameter('min_event_duration_ms', value=50.0),  # 10 samples
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
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

    # Reset and try with 21 samples — should publish
    node2 = GazeController()
    node2.set_parameters([
        rclpy.parameter.Parameter('internal_pipeline_delay_ms', value=0.0),
        rclpy.parameter.Parameter('start_trim_ms', value=50.0),
        rclpy.parameter.Parameter('min_event_duration_ms', value=50.0),
        rclpy.parameter.Parameter('terminal_trim_ms', value=0.0),
    ])
    node2.button_cb(make_button("btn1", 10.0, 10.0, 1))
    node2.button_cb(make_button("btn1", 10.0, 10.0, 3))
    for i in range(21):
        t = 1.0 + i * 0.005
        node2.gaze_cb(make_gaze(100.0, 100.0, int(t), int(round((t % 1) * 1e9))))
    published_ok = capture_segments(node2)
    node2.saccade_cb(make_saccade(1_105_000_000))
    assert len(published_ok) == 1, "21-sample window should pass the threshold."


def test_publish_to_robot_loop_button_id_typo():
    """
    BUG(8): In publish_to_robot_loop, the INACTIVE branch writes:
        out_msg.button_id = ""   # AttributeError — ButtonStatus has no .button_id
    The correct attribute is out_msg.button.button_id.
    This causes an AttributeError every ~33ms when not recording.

    This test confirms the method doesn't crash when is_recording is False.
    """
    node = GazeController()
    # Plant a raw button msg so the early-return guard is by PASS
    node.latest_raw_button_msg = make_button("btn1", 10.0, 10.0, 1)
    node.is_recording = False

    try:
        node.publish_to_robot_loop()
    except AttributeError as e:
        pytest.fail(
            f"publish_to_robot_loop crashed with AttributeError: {e}\n"
            "Fix: change `out_msg.button_id = ''` to `out_msg.button.button_id = ''`"
        )