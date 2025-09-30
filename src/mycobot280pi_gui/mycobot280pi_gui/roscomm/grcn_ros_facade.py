
"""
Defines the ROSCommunication class, which acts as a Façade.

This class is the single, clean entry point for the GUI to interact with the
entire ROS backend. It hides the complexity of the underlying nodes, handlers,
and threading.

Key Responsibilities:
- Inherits from QObject to provide thread-safe PyQt signals to the GUI.
- Owns and manages the lifecycle of the main ROS node (ROSOrchestratorNode).
- Spins the ROS node in a separate, non-blocking background thread.
- Exposes a high-level, clean API (public methods) for the GUI to call.
- Delegates the actual ROS work from its public methods to the specialized
  handlers (TopicHandler, ServiceClientHandler, etc.).
"""

from rclpy.executors import MultiThreadedExecutor
import threading
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

# Import the orchestrator node from its new file
from .grcn_ros_node import ROSOrchestratorNode

# Import message types required for pyqtSignal definitions
from sensor_msgs.msg import JointState
from mycobot280pi_interfaces.msg import ManyDetectedObjects


class ROSCommunication(QObject):
    """The Facade class that bridges the GUI with the ROS backend."""

    # --- Signals for ROS -> GUI Communication ---
    # These signals are emitted from the ROS thread and safely received by the GUI thread.
    undistorted_image_received = pyqtSignal(np.ndarray)
    annotated_image_received = pyqtSignal(np.ndarray)
    detected_objects_received = pyqtSignal(ManyDetectedObjects)
    joint_state_received = pyqtSignal(JointState)
    simple_command_response_received = pyqtSignal(bool, str) 
    action_feedback = pyqtSignal(str)
    action_result = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. The Facade creates its internal ROS node orchestrator.
        #    It passes 'self' so that the handlers can get a reference
        #    to this facade and emit its signals.
        self._ros_node = ROSOrchestratorNode(self)
        
        # 2. The threading model remains the same: a MultiThreadedExecutor
        #    runs in a background thread to spin the node.
        self.executor = MultiThreadedExecutor()
        self.executor.add_node(self._ros_node)
        self.ros_thread = threading.Thread(target=self.executor.spin)
        self.ros_thread.daemon = True # Ensures thread exits when main app exits
        self.ros_thread.start()
        
        self.get_logger().info("ROS Communication Facade is ready.")

    # --- Public API Methods for GUI -> ROS Communication ---
    # The MainWindow will call these simple methods.
    
    def get_logger(self):
        """Provides the GUI with access to the ROS logger."""
        return self._ros_node.get_logger()
    
    def publish_four_points(self, points: np.ndarray):
        """Delegate point publishing to the TopicHandler."""
        self._ros_node.topic_handler.publish_perspective_points(points)

    def call_simple_command(self, 
                            command_type: str,
                            coords: list = None, 
                            joint_angles: list = None,
                            speed: int = 0, 
                            r: int = 0, 
                            g: int = 0, 
                            b: int = 0, 
                            vacuum_pin1_level: int = 0, 
                            vacuum_pin2_level: int = 0, 
                            extra_strings: list = None, 
                            extra_floats: list = None, 
                            extra_ints: list = None):
        
        """
        Delegate unified simple command service call to the ServiceClientHandler.
        
        Note: The command_type is mandatory, all other parameters default to safe values.
        """
        def ensure_list(value):
            """Return [] if value is None, otherwise return value itself."""
            return [] if value is None else value

        # Always safe: never None
        coords = ensure_list(coords)
        joint_angles = ensure_list(joint_angles)
        extra_strings = ensure_list(extra_strings)
        extra_floats = ensure_list(extra_floats)
        extra_ints = ensure_list(extra_ints) 
        
        # Delegate the call to the ServiceClientHandler instance
        self._ros_node.service_handler.call_simple_command(
            command_type, 
            coords, 
            joint_angles,
            speed, 
            r, 
            g, 
            b, 
            vacuum_pin1_level, 
            vacuum_pin2_level, 
            extra_strings, 
            extra_floats, 
            extra_ints
        )
        

        
    def send_complex_goal(self, objects_to_move, target_positions, target_orientation):
        """Delegate complex goal action call to the ActionClientHandler."""
        self._ros_node.action_handler.send_goal(objects_to_move, target_positions, target_orientation)

    def cancel_complex_goal(self):
        """Delegate goal cancellation to the ActionClientHandler."""
        self._ros_node.action_handler.cancel_goal()

    def shutdown(self):
        """Handles the clean shutdown of the ROS components."""
        self.get_logger().info("Shutting down ROS executor and node...")
        self.executor.shutdown()
        self._ros_node.destroy_node()
