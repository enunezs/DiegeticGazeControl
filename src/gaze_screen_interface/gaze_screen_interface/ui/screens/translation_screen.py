"""
Translation Mode Screen
Directional controls for robot translation with back button
"""

from PySide6.QtWidgets import QLabel, QGridLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from .base_screen import BaseScreen


class TranslationScreen(BaseScreen):
    """
    Translation control screen with directional arrows and back button.
    """

    def __init__(self, parent=None):
        super().__init__("translation", parent)
        self._setup_ui()

    def _setup_ui(self):
        """Create the translation screen UI."""
        # Title
        title = QLabel("Translation Mode", self)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #ecf0f1; margin: 10px;")
        self.layout.addWidget(title)

        # Directional controls in grid
        controls_widget = QWidget()
        controls_layout = QGridLayout(controls_widget)
        controls_layout.setSpacing(10)

        # Up button
        up_btn = self.add_gaze_button(
            "btn_trans_up", "↑ Up", lambda: self._execute_translation("up")
        )
        controls_layout.addWidget(up_btn, 0, 1, alignment=Qt.AlignCenter)

        # Left button
        left_btn = self.add_gaze_button(
            "btn_trans_left", "← Left", lambda: self._execute_translation("left")
        )
        controls_layout.addWidget(left_btn, 1, 0, alignment=Qt.AlignCenter)

        # Right button
        right_btn = self.add_gaze_button(
            "btn_trans_right", "Right →", lambda: self._execute_translation("right")
        )
        controls_layout.addWidget(right_btn, 1, 2, alignment=Qt.AlignCenter)

        # Down button
        down_btn = self.add_gaze_button(
            "btn_trans_down", "↓ Down", lambda: self._execute_translation("down")
        )
        controls_layout.addWidget(down_btn, 2, 1, alignment=Qt.AlignCenter)

        # Forward/Back in 3D space
        forward_btn = self.add_gaze_button(
            "btn_trans_forward",
            "⊕ Forward",
            lambda: self._execute_translation("forward"),
        )
        controls_layout.addWidget(forward_btn, 1, 1, alignment=Qt.AlignCenter)

        back_3d_btn = self.add_gaze_button(
            "btn_trans_backward",
            "⊖ Backward",
            lambda: self._execute_translation("backward"),
        )
        controls_layout.addWidget(back_3d_btn, 3, 1, alignment=Qt.AlignCenter)

        self.layout.addWidget(controls_widget)
        self.layout.addStretch()

        # Back to main menu button
        back_btn = self.add_gaze_button(
            "btn_back_main",
            "✕ Back to Main Menu",
            lambda: self.navigate_to.emit("main_menu"),
        )
        back_btn.setMaximumWidth(250)
        self.layout.addWidget(back_btn, alignment=Qt.AlignCenter)

    def _execute_translation(self, direction: str):
        """
        Execute translation command.
        In real implementation, this would publish ROS2 commands.
        """
        print(f"Translation command: {direction}")
        self.button_activated.emit(f"translate_{direction}")
