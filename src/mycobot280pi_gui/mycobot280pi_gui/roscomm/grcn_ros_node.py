
"""
Defines the ROSOrchestratorNode class.

This class is the central rclpy.Node for the application. It does not handle
any specific ROS communication logic itself. Instead, its sole responsibility
is to act as an orchestrator:
- It creates instances of all specialized handler classes (Topic, Service, Action).
- It provides the necessary context (itself as a Node instance and a reference
  to the facade for signal emitting) to each handler.
- It is the node that gets spun by the executor in the background thread.
"""

from rclpy.node import Node
from PyQt5.QtCore import QObject

# Import the specialized handlers from the 'handlers' sub-package
from .handlers.grcn_topic_subscriber_publisher_handler import TopicHandler
from .handlers.grcn_service_client_handler import ServiceClientHandler
from .handlers.grcn_action_client_handler import ActionClientHandler


class ROSOrchestratorNode(Node):
    """The central ROS node that creates and manages all communication handlers."""

    def __init__(self, facade: QObject):
        """
        Initializes the node and all its specialized handlers.
        
        Args:
            facade: A reference to the ROSCommunication (facade) instance,
                    which is passed down to the handlers so they can emit its signals.
        """
        super().__init__('grcn_gui_orchestrator_node')
        self.get_logger().info("ROS Orchestrator Node is initializing...")
        
        # Create an instance of each handler, passing the necessary context
        self.topic_handler = TopicHandler(self, facade)
        self.service_handler = ServiceClientHandler(self, facade)
        self.action_handler = ActionClientHandler(self, facade)
        
        self.get_logger().info("All ROS handlers have been successfully created.")
