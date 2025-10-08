"""
Main Menu Screen
Entry point with three mode selection buttons
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from .base_screen import BaseScreen


class MainMenuScreen(BaseScreen):
    """
    Main menu with three robot operation modes.
    """

    def __init__(self, parent=None):
        super().__init__("main_menu", parent)
        self._setup_ui()

    def _setup_ui(self):
        """Create the main menu UI."""
        # Title
        title = QLabel("Gaze Control Interface", self)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #ecf0f1; margin: 20px;")
        self.layout.addWidget(title)

        # Spacer
        self.layout.addStretch()

        # Mode buttons
        translation_btn = self.add_gaze_button(
            "btn_translation",
            "Translation Mode",
            lambda: self.navigate_to.emit("translation"),
        )
        self.layout.addWidget(translation_btn, alignment=Qt.AlignCenter)

        rotation_btn = self.add_gaze_button(
            "btn_rotation", "Rotation Mode", lambda: self.navigate_to.emit("rotation")
        )
        self.layout.addWidget(rotation_btn, alignment=Qt.AlignCenter)

        grasping_btn = self.add_gaze_button(
            "btn_grasping", "Grasping Mode", lambda: self.navigate_to.emit("grasping")
        )
        self.layout.addWidget(grasping_btn, alignment=Qt.AlignCenter)

        # Spacer
        self.layout.addStretch()

        # Info text
        info = QLabel("Select a mode using gaze or mouse", self)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #95a5a6; margin: 10px;")
        self.layout.addWidget(info)
