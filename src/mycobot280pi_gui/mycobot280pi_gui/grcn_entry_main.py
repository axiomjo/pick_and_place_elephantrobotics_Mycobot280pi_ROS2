"""
grcn_entry_main.py - Main entry point for the GUI node.

This script's ONLY job is to initialize rclpy, initialize the QApplication,
create an instance of the AppOrchestrator, and start the event loop.
"""

import sys
import rclpy
from PyQt5.QtWidgets import QApplication

# Import the main orchestrator class
from .app_orchestrator_core import AppOrchestrator

def main(args=None):
    """Main function that will be executed by the ROS 2 entry point."""
    # Initialize rclpy once in the main thread
    rclpy.init(args=args)
    
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Create an instance of our orchestrator. This builds the entire application.
    orchestrator = AppOrchestrator()
    
    # Run the application's event loop and capture the exit code
    exit_code = app.exec_()
    
    # The orchestrator's shutdown logic is connected to the window closing,
    # so we don't need to call it explicitly here. rclpy.shutdown() will be
    # handled automatically when the context manager exits.
    
    # Exit the script with the appropriate code
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
