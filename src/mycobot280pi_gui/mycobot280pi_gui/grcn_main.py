"""
grcn_main.py

Main entry point for the gui_robot_control_node.
Initializes the PyQt application and main window, and starts the event loop.
"""
import rclpy
import sys
from PyQt5.QtWidgets import QApplication
from .grcn_pyqt_gui_app import MainWindow

def main():
    
    rclpy.init()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
