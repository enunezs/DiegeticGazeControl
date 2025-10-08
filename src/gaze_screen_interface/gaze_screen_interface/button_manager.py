"""
Button Manager - Manages button states and geometry
Converts between screen coordinates and normalized coordinates for ROS2
"""

from PySide6.QtCore import QRectF
from typing import Dict, List, Tuple


class ButtonManager:
    """
    Manages button geometry and state.
    Converts between screen pixels and normalized [0,1] coordinates.
    """

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.buttons: Dict[str, QRectF] = {}  # button_id -> geometry
        self.button_states: Dict[str, Tuple[int, float]] = (
            {}
        )  # button_id -> (status, percent)

    def update_screen_size(self, width: int, height: int):
        """Update screen dimensions when window is resized."""
        self.screen_width = width
        self.screen_height = height

    def register_button(self, button_id: str, rect: QRectF):
        """
        Register a button with its screen geometry.

        Args:
            button_id: Unique identifier for the button
            rect: QRectF with x, y, width, height in screen pixels
        """
        self.buttons[button_id] = rect

    def unregister_button(self, button_id: str):
        """Remove a button from tracking."""
        self.buttons.pop(button_id, None)
        self.button_states.pop(button_id, None)

    def clear_buttons(self):
        """Clear all registered buttons."""
        self.buttons.clear()
        self.button_states.clear()

    def update_button_state(self, button_id: str, status: int, percent: float):
        """Update the state of a button from ROS2 feedback."""
        self.button_states[button_id] = (status, percent)

    def get_button_state(self, button_id: str) -> Tuple[int, float]:
        """Get current state of a button. Returns (status, percent)."""
        return self.button_states.get(button_id, (0, 0.0))

    def get_buttons_for_ros(self) -> List[dict]:
        """
        Convert all registered buttons to normalized coordinates for ROS2.

        Returns:
            List of dicts suitable for RosBridge.publish_buttons()
        """
        buttons_data = []

        for button_id, rect in self.buttons.items():
            # Normalize coordinates to [0, 1]
            center_x = (rect.center().x()) / self.screen_width
            center_y = (rect.center().y()) / self.screen_height

            # Get corner points (top-left, top-right, bottom-right, bottom-left)
            x_points = [
                rect.left() / self.screen_width,
                rect.right() / self.screen_width,
                rect.right() / self.screen_width,
                rect.left() / self.screen_width,
            ]

            y_points = [
                rect.top() / self.screen_height,
                rect.top() / self.screen_height,
                rect.bottom() / self.screen_height,
                rect.bottom() / self.screen_height,
            ]

            buttons_data.append(
                {
                    "button_id": button_id,
                    "center_x": center_x,
                    "center_y": center_y,
                    "x_points": x_points,
                    "y_points": y_points,
                }
            )

        return buttons_data

    def screen_to_normalized(self, x: float, y: float) -> Tuple[float, float]:
        """Convert screen pixels to normalized [0,1] coordinates."""
        return (x / self.screen_width, y / self.screen_height)

    def normalized_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Convert normalized [0,1] coordinates to screen pixels."""
        return (x * self.screen_width, y * self.screen_height)
