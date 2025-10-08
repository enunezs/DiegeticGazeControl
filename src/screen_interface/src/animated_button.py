from PySide6.QtCore import Qt, QPropertyAnimation, Property, QEasingCurve, QRectF
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
import sys


class AnimatedButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self._radius = 0
        self._max_radius = 100
        self._animation = QPropertyAnimation(self, b"radius", self)
        self._animation.setDuration(400)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._hovering = False

    def enterEvent(self, event):
        self._hovering = True
        self._animation.stop()
        self._animation.setStartValue(self._radius)
        self._animation.setEndValue(self._max_radius)
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovering = False
        self._animation.stop()
        self._animation.setStartValue(self._radius)
        self._animation.setEndValue(0)
        self._animation.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._radius > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            color = QColor(0, 150, 255, 60)  # light blue with transparency
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)

            # Draw circle from center
            center = self.rect().center()
            painter.drawEllipse(QRectF(center.x() - self._radius,
                                       center.y() - self._radius,
                                       self._radius * 2,
                                       self._radius * 2))

    def get_radius(self):
        return self._radius

    def set_radius(self, value):
        self._radius = value
        self.update()

    radius = Property(float, get_radius, set_radius)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Radial Hover Animation")
        self.setFixedSize(400, 300)

        button = AnimatedButton("Hover Me")
        self.setCentralWidget(button)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
