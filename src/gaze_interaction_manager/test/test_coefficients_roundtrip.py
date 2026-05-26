#!/usr/bin/env python3
"""
Resolution-aware round-trip tests for coefficient packing/unpacking.

These tests verify that:
  1. publish_model_update() correctly normalises coefficients by W/2 and H/2
     (not W and H) when packing model parameters.
  2. GazeController.get_correction() correctly recovers the original correction
     at any point on screen.
  3. The round-trip (train → pack → unpack → apply) is accurate across a
     range of screen resolutions.

Run with:

    python3 -m pytest src/gaze_interaction_manager/test/test_coefficients_roundtrip.py -v -s

"""

import os
import sys
import pytest
import numpy as np

import rclpy

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, "..", "scripts")
sys.path.insert(0, scripts_dir)

from spatial_calibration_learner import CalibrationLearner, GazeCorrectionFramework
from gaze_controller import GazeController
from gaze_interaction_manager.msg import CalibrationModel


# ===========================================================================
# Fixtures
# ===========================================================================

RESOLUTIONS = [
    (800, 600),    # Standard 4:3
    (1600, 1200),  # Double standard
    (1920, 1080),  # 16:9 HD
    (2560, 1440),  # 16:9 QHD — non-square half-sizes
    (1024, 768),   # XGA
]


@pytest.fixture(autouse=True)
def ros_setup(tmp_path, monkeypatch):
    rclpy.init()
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    yield
    rclpy.shutdown()


def make_learner(w, h, tmp_path, monkeypatch):
    """Creates a CalibrationLearner configured for the given resolution."""
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    node = CalibrationLearner()
    node.set_parameters([
        rclpy.parameter.Parameter("screen_w", value=float(w)),
        rclpy.parameter.Parameter("screen_h", value=float(h)),
    ])
    node.cfg["screen_w"] = float(w)
    node.cfg["screen_h"] = float(h)
    node.cfg["center_x"] = w / 2.0
    node.cfg["center_y"] = h / 2.0
    for m in node.competitors:
        m.cx = w / 2.0
        m.cy = h / 2.0
    return node


def make_controller(w, h):
    """Creates a GazeController configured for the given resolution."""
    ctrl = GazeController()
    ctrl.set_parameters([
        rclpy.parameter.Parameter("screen_w", value=float(w)),
        rclpy.parameter.Parameter("screen_h", value=float(h)),
    ])
    ctrl.screen_w = float(w)
    ctrl.screen_h = float(h)
    ctrl.center_x = w / 2.0
    ctrl.center_y = h / 2.0
    return ctrl


def pack_and_apply(node, ctrl, winner_idx, params_x, params_y, gaze_x, gaze_y):
    """
    Injects raw params into a competitor, publishes the model update,
    feeds it into the controller, and returns the correction at (gaze_x, gaze_y).
    """
    winner = node.competitors[winner_idx]
    winner.params = {"x": np.array(params_x, dtype=float),
                     "y": np.array(params_y, dtype=float)}
    winner.current_features_x = winner.master_recipe_x
    winner.current_features_y = winner.master_recipe_y
    node.active_idx = winner_idx

    received = []
    node.model_pub.publish = lambda m: received.append(m)
    node.publish_model_update()

    assert len(received) == 1, "publish_model_update did not publish exactly one message"
    ctrl.model_cb(received[0])

    return ctrl.get_correction(float(gaze_x), float(gaze_y))


# ===========================================================================
# Helper: expected correction from raw model coefficients
# ===========================================================================

def expected_bias(px, py):
    """bias model: correction is just the constant offset."""
    return float(px[0]), float(py[0])


def expected_radial_concentric(px, py, cx, cy, gx, gy):
    """Radial Concentric: bias + scale*(daxis/caxis)."""
    dx, dy = gx - cx, gy - cy
    corr_x = px[0] + px[1] * (dx / cx)
    corr_y = py[0] + py[1] * (dy / cy)
    return corr_x, corr_y


def expected_simple_radial(px, py, cx, cy, gx, gy):
    """Simple Radial: bias + coeff*(d*r)/c²  — note coeff[1] for both axes."""
    dx, dy = gx - cx, gy - cy
    r = np.sqrt(dx**2 + dy**2)
    corr_x = px[0] + px[1] * (dx * r) / cx**2
    corr_y = py[0] + py[1] * (dy * r) / cy**2
    return corr_x, corr_y


def expected_radial_complete(px, py, cx, cy, gx, gy):
    """radial_universal: bias + main_radial + cross_radial + main_linear + cross_linear."""
    dx, dy = gx - cx, gy - cy
    r = np.sqrt(dx**2 + dy**2)
    corr_x = (px[0]
              + px[1] * (dx * r) / cx**2
              + px[2] * (dy * r) / cy**2
              + px[3] * dx / cx
              + px[4] * dy / cy
              + px[5])
    corr_y = (py[0]
              + py[1] * (dx * r) / cx**2
              + py[2] * (dy * r) / cy**2
              + py[3] * dx / cx
              + py[4] * dy / cy
              + py[5])
    return corr_x, corr_y


def expected_linear(px, py, cx, cy, gx, gy):
    """Linear: bias + lin_x*(dx/cx) + lin_y*(dy/cy)."""
    dx, dy = gx - cx, gy - cy
    corr_x = px[0] + px[1] * dx / cx + px[2] * dy / cy
    corr_y = py[0] + py[1] * dx / cx + py[2] * dy / cy
    return corr_x, corr_y


# ===========================================================================
# 1. BIAS MODEL
# ===========================================================================

@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_bias_roundtrip(w, h, tmp_path, monkeypatch):
    """Bias correction is resolution-independent (no normalisation needed)."""
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    bias_idx = next(i for i, m in enumerate(node.competitors) if m.name == "Bias")
    BIAS_X, BIAS_Y = 37.5, -22.0

    cx, cy = pack_and_apply(node, ctrl, bias_idx,
                            [BIAS_X], [BIAS_Y],
                            gaze_x=w / 2, gaze_y=h / 2)

    assert cx == pytest.approx(BIAS_X, abs=1e-4), f"Bias X failed at {w}x{h}"
    assert cy == pytest.approx(BIAS_Y, abs=1e-4), f"Bias Y failed at {w}x{h}"


@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_bias_off_center(w, h, tmp_path, monkeypatch):
    """Bias correction is the same everywhere on screen."""
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    bias_idx = next(i for i, m in enumerate(node.competitors) if m.name == "Bias")
    BIAS_X, BIAS_Y = 50.0, 50.0

    # Correction at top-left and bottom-right should be identical
    cx1, cy1 = pack_and_apply(node, ctrl, bias_idx, [BIAS_X], [BIAS_Y],
                               gaze_x=10, gaze_y=10)
    cx2, cy2 = pack_and_apply(node, ctrl, bias_idx, [BIAS_X], [BIAS_Y],
                               gaze_x=w - 10, gaze_y=h - 10)

    assert cx1 == pytest.approx(BIAS_X, abs=1e-4)
    assert cx1 == pytest.approx(cx2, abs=1e-4)
    assert cy1 == pytest.approx(cy2, abs=1e-4)


# ===========================================================================
# 2. RADIAL CONCENTRIC
# ===========================================================================

@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_radial_concentric_roundtrip(w, h, tmp_path, monkeypatch):
    """
    Radial Concentric: trained with dx/cx and dy/cy.
    Packing must divide by W/2 and H/2 (not W and H).
    """
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    rc_idx = next(i for i, m in enumerate(node.competitors)
                  if m.name == "Radial Concentric")

    px = [5.0, 2.0]   # bias=5, radial_scale=2
    py = [3.0, 1.5]

    # Test at a point with clear radial displacement
    gx, gy = w * 0.75, h * 0.25
    cx, cy = pack_and_apply(node, ctrl, rc_idx, px, py, gx, gy)

    exp_x, exp_y = expected_radial_concentric(
        px, py, w / 2, h / 2, gx, gy
    )

    assert cx == pytest.approx(exp_x, abs=1e-3), \
        f"Radial Concentric X failed at {w}x{h}: got {cx}, expected {exp_x}"
    assert cy == pytest.approx(exp_y, abs=1e-3), \
        f"Radial Concentric Y failed at {w}x{h}: got {cx}, expected {exp_y}"


@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_radial_concentric_center_is_bias_only(w, h, tmp_path, monkeypatch):
    """At screen center dx=dy=0, correction should equal bias only."""
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    rc_idx = next(i for i, m in enumerate(node.competitors)
                  if m.name == "Radial Concentric")

    BIAS = 12.0
    cx, cy = pack_and_apply(node, ctrl, rc_idx,
                            [BIAS, 99.0], [BIAS, 99.0],
                            gaze_x=w / 2, gaze_y=h / 2)

    assert cx == pytest.approx(BIAS, abs=1e-3), \
        f"Center correction should be bias-only at {w}x{h}"
    assert cy == pytest.approx(BIAS, abs=1e-3)


# ===========================================================================
# 3. SIMPLE RADIAL
# ===========================================================================

@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_simple_radial_roundtrip(w, h, tmp_path, monkeypatch):
    """
    Simple Radial: feature is (d*r)/c².
    Bug was py[2] instead of py[1]; and W²  instead of (W/2)².
    """
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    sr_idx = next(i for i, m in enumerate(node.competitors)
                  if m.name == "Simple Radial")

    px = [4.0, 3.0]   # [bias, radial_coeff_x]
    py = [2.0, 1.5]   # [bias, radial_coeff_y]

    gx, gy = w * 0.8, h * 0.2
    cx, cy = pack_and_apply(node, ctrl, sr_idx, px, py, gx, gy)

    exp_x, exp_y = expected_simple_radial(px, py, w / 2, h / 2, gx, gy)

    assert cx == pytest.approx(exp_x, abs=1e-3), \
        f"Simple Radial X failed at {w}x{h}: got {cx}, expected {exp_x}"
    assert cy == pytest.approx(exp_y, abs=1e-3), \
        f"Simple Radial Y failed at {w}x{h}: got {cy}, expected {exp_y}"


@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_simple_radial_symmetric(w, h, tmp_path, monkeypatch):
    """
    For equal bias and radial coefficients, correction at (cx+d, cy) and
    (cx-d, cy) should be equal in magnitude and opposite in sign (radial term),
    plus the bias.
    """
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    sr_idx = next(i for i, m in enumerate(node.competitors)
                  if m.name == "Simple Radial")

    px = [0.0, 1.0]
    py = [0.0, 1.0]
    d = w * 0.2

    cx_pos, _ = pack_and_apply(node, ctrl, sr_idx, px, py,
                                gaze_x=w / 2 + d, gaze_y=h / 2)
    cx_neg, _ = pack_and_apply(node, ctrl, sr_idx, px, py,
                                gaze_x=w / 2 - d, gaze_y=h / 2)

    assert cx_pos == pytest.approx(-cx_neg, abs=1e-3), \
        f"Simple Radial not antisymmetric at {w}x{h}"


# ===========================================================================
# 4. RADIAL COMPLETE (radial_universal)
# ===========================================================================

@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_radial_complete_roundtrip(w, h, tmp_path, monkeypatch):
    """
    Radial Complete uses radial_universal.
    All four non-bias terms must be normalised by W/2 or H/2 (squared for radial).
    """
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    rc_idx = next(i for i, m in enumerate(node.competitors)
                  if m.name == "Radial Complete")

    # [bias, dx*r coeff, dy*r coeff (cross), dx coeff, dy coeff, extra_bias]
    px = [0.0, 2.0, 0.5, 4.0, 1.0, 3.0]
    py = [0.0, 0.3, 1.5, 0.8, 3.5, 2.0]

    gx, gy = w * 0.3, h * 0.7
    cx, cy = pack_and_apply(node, ctrl, rc_idx, px, py, gx, gy)

    exp_x, exp_y = expected_radial_complete(px, py, w / 2, h / 2, gx, gy)

    assert cx == pytest.approx(exp_x, rel=1e-4), \
        f"Radial Complete X failed at {w}x{h}: got {cx}, expected {exp_x}"
    assert cy == pytest.approx(exp_y, rel=1e-4), \
        f"Radial Complete Y failed at {w}x{h}: got {cy}, expected {exp_y}"


@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_radial_complete_center_is_bias_only(w, h, tmp_path, monkeypatch):
    """At screen center all radial/linear terms vanish; only bias survives."""
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    rc_idx = next(i for i, m in enumerate(node.competitors)
                  if m.name == "Radial Complete")

    # bias=7, extra_bias=3 → combined=10; all other coeffs are large to catch leakage
    px = [7.0, 50.0, 50.0, 50.0, 50.0, 3.0]
    py = [7.0, 50.0, 50.0, 50.0, 50.0, 3.0]

    cx, cy = pack_and_apply(node, ctrl, rc_idx, px, py,
                            gaze_x=w / 2, gaze_y=h / 2)

    assert cx == pytest.approx(10.0, abs=1e-3), \
        f"Radial Complete center should be bias-only at {w}x{h}: got {cx}"
    assert cy == pytest.approx(10.0, abs=1e-3)


# ===========================================================================
# 5. LINEAR MODEL
# ===========================================================================

@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_linear_roundtrip(w, h, tmp_path, monkeypatch):
    """
    Linear model: bias + lin_x*(dx/cx) + lin_y*(dy/cy).
    Normalisation must use cx=W/2, cy=H/2.
    """
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    lin_idx = next(i for i, m in enumerate(node.competitors) if m.name == "Linear")
    winner = node.competitors[lin_idx]
    # Force full unlock so all three features are active
    winner.current_features_x = winner.master_recipe_x
    winner.current_features_y = winner.master_recipe_y

    px = [5.0, 3.0, 1.0]   # [bias, lin_x_coeff, lin_y_coeff]
    py = [2.0, 0.5, 4.0]

    gx, gy = w * 0.6, h * 0.4
    cx, cy = pack_and_apply(node, ctrl, lin_idx, px, py, gx, gy)

    exp_x, exp_y = expected_linear(px, py, w / 2, h / 2, gx, gy)

    assert cx == pytest.approx(exp_x, abs=1e-3), \
        f"Linear X failed at {w}x{h}: got {cx}, expected {exp_x}"
    assert cy == pytest.approx(exp_y, abs=1e-3), \
        f"Linear Y failed at {w}x{h}: got {cy}, expected {exp_y}"


@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_linear_scales_with_displacement(w, h, tmp_path, monkeypatch):
    """
    Doubling the displacement from center should double the linear component
    of the correction (minus the bias).
    """
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    lin_idx = next(i for i, m in enumerate(node.competitors) if m.name == "Linear")
    winner = node.competitors[lin_idx]
    winner.current_features_x = winner.master_recipe_x
    winner.current_features_y = winner.master_recipe_y

    px = [0.0, 2.0, 0.0]   # pure lin_x, no bias, no lin_y
    py = [0.0, 0.0, 2.0]   # pure lin_y

    d = w * 0.1
    cx1, _ = pack_and_apply(node, ctrl, lin_idx, px, py,
                             gaze_x=w / 2 + d, gaze_y=h / 2)
    cx2, _ = pack_and_apply(node, ctrl, lin_idx, px, py,
                             gaze_x=w / 2 + 2 * d, gaze_y=h / 2)

    assert cx2 == pytest.approx(2 * cx1, rel=1e-4), \
        f"Linear correction did not scale linearly at {w}x{h}"


# ===========================================================================
# 6. NORMALISATION SENSITIVITY: W vs W/2 regression
# ===========================================================================

@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_normalisation_is_half_not_full(w, h, tmp_path, monkeypatch):
    """
    This is the key regression test.
    At screen edge (gx = w, gy = h/2), dx = w/2.
    A lin_x coefficient of 1.0 trained on dx/cx = dx/(w/2) should produce
    correction = 1.0 * (dx / (w/2)) = 1.0 * 1.0 = 1.0 — regardless of resolution.

    If the packing divides by W instead of W/2, the unpacked coefficient is
    halved, and the correction will be 0.5 instead of 1.0.
    """
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    lin_idx = next(i for i, m in enumerate(node.competitors) if m.name == "Linear")
    winner = node.competitors[lin_idx]
    winner.current_features_x = winner.master_recipe_x
    winner.current_features_y = winner.master_recipe_y

    # Set lin_x coefficient = 1.0, no bias, no lin_y
    px = [0.0, 1.0, 0.0]
    py = [0.0, 0.0, 0.0]

    # At gx = w (right edge), dx = w/2, so correction = 1.0 * (w/2)/(w/2) = 1.0
    cx, _ = pack_and_apply(node, ctrl, lin_idx, px, py,
                            gaze_x=float(w), gaze_y=h / 2)

    assert cx == pytest.approx(1.0, abs=1e-4), (
        f"Normalisation bug at {w}x{h}: got {cx:.4f}, expected 1.0. "
        "Likely dividing by W instead of W/2 during packing."
    )


@pytest.mark.parametrize("w,h", RESOLUTIONS)
def test_radial_normalisation_is_half_squared(w, h, tmp_path, monkeypatch):
    """
    For radial terms trained on (dx*r)/cx², the denominator in packing
    must be (W/2)² not W².

    At gx=w, gy=h/2: dx=W/2, dy=0, r=W/2.
    (dx*r)/cx² = (W/2 * W/2)/(W/2)² = 1.0.
    A radial coeff of 1.0 should produce correction = 1.0.
    """
    node = make_learner(w, h, tmp_path, monkeypatch)
    ctrl = make_controller(w, h)

    sr_idx = next(i for i, m in enumerate(node.competitors)
                  if m.name == "Simple Radial")

    px = [0.0, 1.0]
    py = [0.0, 0.0]

    cx, _ = pack_and_apply(node, ctrl, sr_idx, px, py,
                            gaze_x=float(w), gaze_y=h / 2)

    assert cx == pytest.approx(1.0, abs=1e-4), (
        f"Radial normalisation bug at {w}x{h}: got {cx:.4f}, expected 1.0. "
        "Likely dividing by W² instead of (W/2)²."
    )


# ===========================================================================
# 7. CROSS-RESOLUTION INVARIANCE
# ===========================================================================

def test_bias_invariant_across_resolutions(tmp_path, monkeypatch):
    """
    A bias model with the same raw coefficient should produce the same
    correction at the proportionally equivalent screen position,
    regardless of resolution.
    """
    results = []
    for w, h in RESOLUTIONS:
        node = make_learner(w, h, tmp_path, monkeypatch)
        ctrl = make_controller(w, h)
        bias_idx = next(i for i, m in enumerate(node.competitors) if m.name == "Bias")
        cx, cy = pack_and_apply(node, ctrl, bias_idx, [20.0], [15.0],
                                 gaze_x=w / 2, gaze_y=h / 2)
        results.append((cx, cy))

    # All corrections should be the same regardless of resolution
    for cx, cy in results:
        assert cx == pytest.approx(20.0, abs=1e-4)
        assert cy == pytest.approx(15.0, abs=1e-4)


def test_unit_linear_invariant_at_proportional_position(tmp_path, monkeypatch):
    """
    With a unit lin_x coefficient (coeff=1.0, no bias), correction at
    x = 3/4 * W (dx = W/4) should equal 0.5 at ALL resolutions.
    (dx/cx = (W/4)/(W/2) = 0.5)
    """
    results = []
    for w, h in RESOLUTIONS:
        node = make_learner(w, h, tmp_path, monkeypatch)
        ctrl = make_controller(w, h)
        lin_idx = next(i for i, m in enumerate(node.competitors) if m.name == "Linear")
        winner = node.competitors[lin_idx]
        winner.current_features_x = winner.master_recipe_x
        winner.current_features_y = winner.master_recipe_y

        cx, _ = pack_and_apply(node, ctrl, lin_idx,
                                [0.0, 1.0, 0.0], [0.0, 0.0, 0.0],
                                gaze_x=w * 0.75, gaze_y=h / 2)
        results.append(cx)

    for cx in results:
        assert cx == pytest.approx(0.5, abs=1e-4), \
            f"Unit linear correction not invariant across resolutions: {results}"