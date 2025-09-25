"""
grcn_main.py

Main entry point for the gui_robot_control_node.
Initializes the PyQt application and main window, and starts the event loop.
"""
import rclpy
import sys
from PyQt5.QtWidgets import QApplication
from .grcn_gui_main_window import MainWindow

def main():
    
    rclpy.init()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit_code = app.exec_()
    rclpy.shutdown()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
