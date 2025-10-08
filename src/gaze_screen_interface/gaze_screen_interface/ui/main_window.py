"""
Main Window
Manages screen navigation and integrates ROS2 communication
"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen

from typing import Dict

from ..ros_bridge import RosBridge
from ..button_manager import ButtonManager
from .screens.main_menu import MainMenuScreen
from .screens.translation_screen import TranslationScreen
from .screens.base_screen import BaseScreen


class GazeDebugOverlay(QWidget):
    """Transparent overlay to display gaze point for debugging."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.gaze_x = -100
        self.gaze_y = -100
        self.show_gaze = True

    def update_gaze(self, x: float, y: float):
        """Update gaze position in screen coordinates."""
        self.gaze_x = x
        self.gaze_y = y
        self.update()

    def paintEvent(self, event):
        """Draw gaze crosshair."""
        if not self.show_gaze or self.gaze_x < 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw crosshair
        pen = QPen(QColor(255, 0, 0, 200), 2)
        painter.setPen(pen)

        size = 20
        painter.drawLine(
            int(self.gaze_x - size),
            int(self.gaze_y),
            int(self.gaze_x + size),
            int(self.gaze_y),
        )
        painter.drawLine(
            int(self.gaze_x),
            int(self.gaze_y - size),
            int(self.gaze_x),
            int(self.gaze_y + size),
        )

        # Draw circle
        painter.drawEllipse(int(self.gaze_x - 5), int(self.gaze_y - 5), 10, 10)

        painter.end()


class MainWindow(QMainWindow):
    """
    Main application window.
    Manages screen navigation, ROS2 integration, and button publishing.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gaze Control Interface")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #1a1a1a;")

        # Initialize ROS2 bridge
        self.ros_bridge = RosBridge("gaze_screen_interface")

        # Initialize button manager
        self.button_manager = ButtonManager(self.width(), self.height())

        # Setup UI
        self._setup_ui()

        # Connect ROS2 signals
        self.ros_bridge.button_status_received.connect(self._on_button_status)
        self.ros_bridge.gaze_point_received.connect(self._on_gaze_update)

        # Timer for ROS2 spinning
        self.ros_timer = QTimer(self)
        self.ros_timer.timeout.connect(lambda: self.ros_bridge.spin_once(0.01))
        self.ros_timer.start(10)  # 100 Hz

        # Timer for button publishing (when geometry changes)
        self.publish_timer = QTimer(self)
        self.publish_timer.timeout.connect(self._publish_buttons)
        self.publish_timer.setSingleShot(True)

        # Show main menu
        self.navigate_to_screen("main_menu")

    def _setup_ui(self):
        """Setup the main UI structure."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Status bar for debug info
        self.status_label = QLabel("ROS2: Connecting...")
        self.status_label.setStyleSheet(
            "color: #95a5a6; padding: 5px; background-color: #2c3e50;"
        )
        layout.addWidget(self.status_label)

        # Stacked widget for screen navigation
        self.screen_stack = QStackedWidget()
        layout.addWidget(self.screen_stack)

        # Create screens
        self.screens: Dict[str, int] = {}  # screen_name -> stack index

        # Main menu
        main_menu = MainMenuScreen()
        main_menu.navigate_to.connect(self.navigate_to_screen)
        main_menu.buttons_changed.connect(self._schedule_button_publish)
        self.screens["main_menu"] = self.screen_stack.addWidget(main_menu)

        # Translation screen
        translation = TranslationScreen()
        translation.navigate_to.connect(self.navigate_to_screen)
        translation.buttons_changed.connect(self._schedule_button_publish)
        self.screens["translation"] = self.screen_stack.addWidget(translation)

        # TODO: Add rotation and grasping screens

        # Gaze debug overlay
        self.gaze_overlay = GazeDebugOverlay(central)
        self.gaze_overlay.setGeometry(central.rect())

    def navigate_to_screen(self, screen_name: str):
        """Navigate to a different screen."""
        if screen_name not in self.screens:
            print(f"Warning: Screen '{screen_name}' not found")
            return

        # Exit current screen
        current_widget = self.screen_stack.currentWidget()
        if isinstance(current_widget, BaseScreen):
            current_widget.on_screen_exit()

        # Switch to new screen
        self.screen_stack.setCurrentIndex(self.screens[screen_name])

        # Enter new screen
        new_widget = self.screen_stack.currentWidget()
        if isinstance(new_widget, BaseScreen):
            new_widget.on_screen_enter()

        print(f"Navigated to: {screen_name}")

    def _schedule_button_publish(self):
        """Schedule button publishing (debounced)."""
        self.publish_timer.start(100)  # 100ms debounce

    def _publish_buttons(self):
        """Collect all visible buttons and publish to ROS2."""
        self.button_manager.clear_buttons()

        current_screen = self.screen_stack.currentWidget()
        if not isinstance(current_screen, BaseScreen):
            return

        # Get interactable buttons from current screen
        buttons = current_screen.get_interactable_buttons()

        for button_id, button_widget in buttons.items():
            # Get global geometry
            global_pos = button_widget.mapTo(self, button_widget.rect().topLeft())
            rect = button_widget.rect()
            rect.moveTopLeft(global_pos)

            self.button_manager.register_button(button_id, rect)

        # Publish to ROS2
        buttons_data = self.button_manager.get_buttons_for_ros()
        self.ros_bridge.publish_buttons(buttons_data)

        self.status_label.setText(
            f"ROS2: Published {len(buttons_data)} buttons | "
            f"Screen: {current_screen.screen_name}"
        )

    def _on_button_status(self, button_id: str, status: int, percent: float):
        """Handle button status update from ROS2."""
        self.button_manager.update_button_state(button_id, status, percent)

        # Update visual feedback on current screen
        current_screen = self.screen_stack.currentWidget()
        if isinstance(current_screen, BaseScreen):
            current_screen.update_button_status(button_id, status, percent)

    def _on_gaze_update(self, x: float, y: float):
        """Handle gaze point update from ROS2."""
        # Convert normalized to screen coordinates
        screen_x, screen_y = self.button_manager.normalized_to_screen(x, y)
        self.gaze_overlay.update_gaze(screen_x, screen_y)

    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)

        # Update button manager with new size
        self.button_manager.update_screen_size(self.width(), self.height())

        # Update gaze overlay geometry
        self.gaze_overlay.setGeometry(self.centralWidget().rect())

        # Republish buttons with new coordinates
        self._schedule_button_publish()

    def closeEvent(self, event):
        """Clean shutdown."""
        self.ros_timer.stop()
        self.ros_bridge.shutdown()
        event.accept()
