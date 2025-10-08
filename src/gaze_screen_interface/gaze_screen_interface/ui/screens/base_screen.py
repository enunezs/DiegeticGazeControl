"""
Base Screen Class
Abstract base class for all screens in the interface
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from typing import Dict
from ..widgets.gaze_button import GazeButton


class BaseScreen(QWidget):
    """
    Abstract base class for screens.
    Handles button registration and provides hooks for subclasses.
    """

    # Signals
    buttons_changed = Signal()  # Emitted when button layout changes
    navigate_to = Signal(str)  # Emitted to request navigation (screen_name)
    button_activated = Signal(
        str
    )  # Emitted when button is clicked/activated (button_id)

    def __init__(self, screen_name: str, parent=None):
        super().__init__(parent)
        self.screen_name = screen_name
        self.buttons: Dict[str, GazeButton] = {}
        self.layout = QVBoxLayout(self)

    def add_gaze_button(self, button_id: str, text: str, callback=None) -> GazeButton:
        """
        Create and add a gaze-enabled button to this screen.

        Args:
            button_id: Unique identifier for the button
            text: Display text
            callback: Optional callback function when button is activated

        Returns:
            The created GazeButton
        """
        btn = GazeButton(button_id, text, self)

        # Connect click signal
        if callback:
            btn.clicked.connect(callback)
        else:
            btn.clicked.connect(lambda: self._default_button_action(button_id))

        self.buttons[button_id] = btn
        return btn

    def _default_button_action(self, button_id: str):
        """Default action when button is clicked."""
        print(f"Button activated: {button_id}")
        self.button_activated.emit(button_id)

    def get_all_buttons(self) -> Dict[str, GazeButton]:
        """Return all buttons on this screen."""
        return self.buttons

    def update_button_status(self, button_id: str, status: int, percent: float):
        """Update visual state of a button from ROS2 feedback."""
        if button_id in self.buttons:
            self.buttons[button_id].set_status(status, percent)

            # Simulate click when button becomes active
            if status == GazeButton.BUTTON_ACTIVE:
                self.buttons[button_id].click()
            if status == GazeButton.BUTTON_HOVER:
                self.buttons[button_id].set_hovered(True)
            if status == GazeButton.BUTTON_INACTIVE:
                self.buttons[button_id].set_hovered(False)

    def on_screen_enter(self):
        """Called when this screen becomes active."""
        self.buttons_changed.emit()

    def on_screen_exit(self):
        """Called when leaving this screen."""
        pass

    def get_interactable_buttons(self) -> Dict[str, GazeButton]:
        """
        Return only interactable buttons (for overlay support).
        Override in subclasses if some buttons should be disabled.
        """
        return self.buttons
