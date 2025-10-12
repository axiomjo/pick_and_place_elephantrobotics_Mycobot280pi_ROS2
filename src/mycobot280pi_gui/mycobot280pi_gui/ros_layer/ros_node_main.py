"""
ros_node_main.py - Defines the ROS_Node_Main class.

This class is the central rclpy.Node for the application. It does not handle
any specific ROS communication logic itself. Instead, its sole responsibility
is to act as an orchestrator:
- It creates instances of all specialized handler classes (Topic, Service, Action).
- It provides the necessary context (itself as a Node instance) to each handler.
- It is the node that gets spun by the executor in the background thread.
"""

from rclpy.node import Node
from PyQt5.QtCore import QObject

# Import the specialized handlers from their new locations
from .handlers_ros.topic_hdlr import TopicHandler
from .handlers_ros.service_client_hdlr import ServiceClientHandler
from .handlers_ros.action_client_hdlr import ActionClientHandler

class ROS_Node_Main(Node):
    """The central ROS node that creates and manages all communication handlers."""

    def __init__(self, facade):
        # (facade: QObject) -> None
        """
        Initializes the node and all its specialized handlers.

        Args:
            facade: A reference to the ROS_Facade_Bridge instance,
                    which is passed down to the handlers so they can emit its signals.
        """
        super().__init__('gui_robot_control_node') 
        self.get_logger().info("ROS Orchestrator Node is initializing...")
        
        # Create an instance of each handler, passing the necessary context
        self.topic_handler = TopicHandler(self, facade)
        self.service_handler = ServiceClientHandler(self, facade)
        self.action_handler = ActionClientHandler(self, facade)
        
        self.get_logger().info("All ROS handlers have been successfully created.")
