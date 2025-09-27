"""
grcn_main.py

Main entry point for the gui_robot_control_node.
Initializes the PyQt application, initialize ROS, create the application and the main window, and start everything
"""
import sys
import threading
import rclpy
from rclpy.executors import MultiThreadedExecutor
from PyQt5.QtWidgets import QApplication

#from other grcn files
from .grcn_ros_communication import ROSCommunication
from .grcn_gui_main_window import MainWindow


def main(args=None):
    rclpy.init(args=args)
    
    # Standard ROS2 + PyQt5 integration
    app = QApplication(sys.argv)
    
    # 1. Create the ROS 2 node
    ros_communication = ROSCommunication()
    
    # 2. Create the GUI, passing the node to it
    main_window = MainWindow(ros_communication)
    main_window.show()
    

    try:
        # Start the Qt event loop (this blocks)
        sys.exit(app.exec_())
    finally:
        # Cleanup
        print("Shutting down ROS 2 node...")
        executor.shutdown()
        ros_communication.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
