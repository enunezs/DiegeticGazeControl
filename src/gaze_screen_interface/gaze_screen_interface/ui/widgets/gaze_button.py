"""
Custom Gaze Button Widget
Animated button that responds to gaze dwell progress and mouse interaction
"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont


class GazeButton(QPushButton):
    """
    Custom button with visual feedback for gaze dwell progress.
    Shows a circular progress indicator around the button.
    """

    # Button status constants (matching ROS message)
    BUTTON_INACTIVE = 0
    BUTTON_ACTIVE = 1
    BUTTON_HOVER = 2

    def __init__(self, button_id: str, text: str = "", parent=None):
        super().__init__(text, parent)

        self.button_id = button_id
        self._dwell_percent = 0.0
        self._status = self.BUTTON_INACTIVE

        # Styling
        self.setMinimumSize(200, 80)
        self.setFont(QFont("Arial", 16, QFont.Bold))
        self.setCursor(Qt.PointingHandCursor)

        # Animation for visual feedback
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(150)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)

        self._apply_style()

    def _apply_style(self):
        """Apply base stylesheet."""
        self.setStyleSheet(
            """
            GazeButton {
                background-color: #2c3e50;
                color: white;
                border: 3px solid #34495e;
                border-radius: 15px;
                padding: 10px;
            }
            GazeButton:hover {
                background-color: #34495e;
                border-color: #3498db;
            }
            GazeButton:pressed {
                background-color: #1a252f;
            }
        """
        )

    @Property(float)
    def dwell_percent(self):
        return self._dwell_percent

    @dwell_percent.setter
    def dwell_percent(self, value):
        self._dwell_percent = max(0.0, min(1.0, value))
        self.update()  # Trigger repaint

    def set_status(self, status: int, percent: float):
        """
        Update button status from ROS2 feedback.

        Args:
            status: BUTTON_INACTIVE, BUTTON_HOVER, or BUTTON_ACTIVE
            percent: Dwell progress [0.0 - 1.0]
        """
        self._status = status
        self.dwell_percent = percent

        # Visual feedback based on status
        if status == self.BUTTON_ACTIVE:
            self._trigger_activation_animation()

    def _trigger_activation_animation(self):
        """Animate button when activated."""
        original = self.geometry()
        # Slight scale up effect
        expanded = QRectF(
            original.x() - 5,
            original.y() - 5,
            original.width() + 10,
            original.height() + 10,
        )

        self.scale_animation.setStartValue(original)
        self.scale_animation.setKeyValueAt(0.5, expanded.toRect())
        self.scale_animation.setEndValue(original)
        self.scale_animation.start()

    def paintEvent(self, event):
        """Custom paint to draw dwell progress indicator."""
        super().paintEvent(event)

        if self._dwell_percent > 0.0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw circular progress arc
            rect = self.rect().adjusted(5, 5, -5, -5)

            # Background arc
            pen = QPen(QColor(100, 100, 100, 100), 4)
            painter.setPen(pen)
            painter.drawArc(rect, 90 * 16, -360 * 16)

            # Progress arc
            if self._status == self.BUTTON_HOVER:
                color = QColor(52, 152, 219)  # Blue
            elif self._status == self.BUTTON_ACTIVE:
                color = QColor(46, 204, 113)  # Green
            else:
                color = QColor(52, 152, 219)

            pen = QPen(color, 4)
            painter.setPen(pen)

            span_angle = -int(360 * 16 * self._dwell_percent)
            painter.drawArc(rect, 90 * 16, span_angle)

            painter.end()

    def get_geometry_rect(self) -> QRectF:
        """Get button geometry as QRectF for ButtonManager."""
        return QRectF(self.geometry())
