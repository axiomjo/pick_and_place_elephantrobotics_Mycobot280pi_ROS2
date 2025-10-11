
"""
Main entry point for the GUI node.

This script's ONLY job is to initialize rclpy, initialize the QApplication,
create an instance of the MainWindow, and start the event loop.
"""

import sys
import rclpy
from PyQt5.QtWidgets import QApplication

# Import MainWindow from its new location within the 'gui' sub-package
from mycobot280pi_gui.gui.grcn_main_window import MainWindow


def main(args=None):
    """Main function that will be executed by the ROS 2 entry point."""
    # Initialize rclpy once in the main thread
    rclpy.init(args=args)
    
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Create an instance of our main window.
    # Note that we no longer pass anything to its constructor.
    window = MainWindow()
    window.show()
    
    # Run the application's event loop and capture the exit code
    exit_code = app.exec_()
    
    # Exit the script with the appropriate code
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
