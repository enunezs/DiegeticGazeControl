"""
Main Entry Point
Launches the Gaze Screen Interface application
"""

import sys
from PySide6.QtWidgets import QApplication
from gaze_screen_interface.ui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Gaze Control Interface")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
