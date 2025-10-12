"""
ros_facade_bridge.py - Defines the ROS_Facade_Bridge class.

This class is the single, clean entry point for the GUI to interact with the
entire ROS backend. It acts as a "Facade," hiding the complexity of the
underlying nodes, handlers, and threading from the rest of the application.
"""

from rclpy.executors import MultiThreadedExecutor
import threading
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

# Import the main ROS node from its new location
from .ros_node_main import ROS_Node_Main

# Import message types required for pyqtSignal definitions
from mycobot280pi_interfaces.msg import ManyDetectedObjects, JointAnglesArray

class ROS_Facade_Bridge(QObject):
    """The Facade class that bridges the GUI/Controllers with the ROS backend."""

    # --- Signals for ROS -> GUI/Controller Communication ---
    # These signals are emitted from the ROS thread and safely received by the GUI thread.
    undistorted_image_received = pyqtSignal(np.ndarray)
    annotated_image_received = pyqtSignal(np.ndarray)
    detected_objects_received = pyqtSignal(ManyDetectedObjects)
    joint_angles_received = pyqtSignal(JointAnglesArray)
    simple_command_response_received = pyqtSignal(bool, str) 
    action_feedback = pyqtSignal(str)
    action_result = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. The Facade creates its internal ROS node orchestrator.
        #    It passes 'self' so that the handlers can get a reference
        #    to this facade and emit its signals[cite: 22].
        self._ros_node = ROS_Node_Main(self)
        
        # 2. A MultiThreadedExecutor runs in a background thread to spin the node[cite: 24].
        self.executor = MultiThreadedExecutor()
        self.executor.add_node(self._ros_node)
        self.ros_thread = threading.Thread(target=self.executor.spin)
        self.ros_thread.daemon = True # Ensures thread exits when main app exits
        self.ros_thread.start()
        
        self.get_logger().info("ROS Communication Facade is ready.")

    # --- Public API Methods for Controller -> ROS Communication ---
    # The Controllers will call these simple methods.

    def get_logger(self):
        """Provides access to the ROS logger."""
        return self._ros_node.get_logger()
    
    def publish_four_points(self, points): # (points: np.ndarray) -> None
        """Delegate point publishing to the TopicHandler."""
        self._ros_node.topic_handler.publish_perspective_points(points)

    def call_simple_command(self, **kwargs):
        """
        Delegate a unified simple command service call to the ServiceClientHandler.
        This uses keyword arguments for flexibility.
        """
        self._ros_node.service_handler.call_simple_command(**kwargs)
        
    def send_complex_goal(self, objects_to_move, target_positions, target_orientation):
        """Delegate complex goal action call to the ActionClientHandler[cite: 34]."""
        self._ros_node.action_handler.send_goal(objects_to_move, target_positions, target_orientation)

    def cancel_complex_goal(self):
        """Delegate goal cancellation to the ActionClientHandler."""
        self._ros_node.action_handler.cancel_goal()

    def shutdown(self):
        """Handles the clean shutdown of the ROS components."""
        self.get_logger().info("Shutting down ROS executor and node...")
        self.executor.shutdown()
        self._ros_node.destroy_node()
