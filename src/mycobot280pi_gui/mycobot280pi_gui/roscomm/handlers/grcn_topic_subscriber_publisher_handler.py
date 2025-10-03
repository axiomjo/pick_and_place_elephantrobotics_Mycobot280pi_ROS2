
"""
Defines the TopicHandler class.

This class encapsulates all logic for ROS 2 topic communication, including
all publishers and subscribers for the application. It acts as the central
point for incoming and outgoing topic-based data streams.
"""

import rclpy.node
from PyQt5.QtCore import QObject
from cv_bridge import CvBridge
import numpy as np

# Import all required message types
from sensor_msgs.msg import Image, JointState
from mycobot280pi_interfaces.msg import Point2D, Point2DArray, ManyDetectedObjects

# --- Constants for topic names ---
TOPIC_UNDISTORTED_IMAGE = '/vision/msg_undistorted_image'
TOPIC_DETECTED_OBJECTS = '/vision/msg_detected_objects'
TOPIC_ANNOTATED_IMAGE = '/vision/msg_annotated_image'
TOPIC_JOINT_ANGLES = '/robot/msg_joint_angles'
TOPIC_FOUR_POINTS = '/gui/msg_four_perspective_points'


class TopicHandler:
    """Manages all publishers and subscribers for the node."""

    def __init__(self, node: rclpy.node.Node, facade: QObject):
        """
        Initializes all publishers and subscribers.
        
        Args:
            node: The ROSOrchestratorNode instance to create topics on.
            facade: The ROSCommunication facade instance to emit signals.
        """
        self._node = node
        self._facade = facade
        self._bridge = CvBridge()
        
        # --- Publishers ---
        self._points_pub = self._node.create_publisher(
            msg_type=Point2DArray,
            topic=TOPIC_FOUR_POINTS,
            qos_profile=10
        )
        
        # --- Subscribers ---
        self._node.create_subscription(
            msg_type=Image,
            topic=TOPIC_UNDISTORTED_IMAGE,
            callback=self._undistorted_cb,
            qos_profile=10
        )
        self._node.create_subscription(
            msg_type=Image,
            topic=TOPIC_ANNOTATED_IMAGE,
            callback=self._annotated_cb,
            qos_profile=10
        )
        self._node.create_subscription(
            msg_type=ManyDetectedObjects,
            topic=TOPIC_DETECTED_OBJECTS,
            callback=self._objects_cb,
            qos_profile=10
        )
        self._node.create_subscription(
            msg_type=JointState,
            topic=TOPIC_JOINT_ANGLES,
            callback=self._joints_cb,
            qos_profile=10
        )
    # --- Public Methods (called by the Facade) ---

    def publish_perspective_points(self, points: np.ndarray):
        """Constructs and publishes a Point2DArray message."""
        msg = Point2DArray()
        for x, y in points:
            msg.points.append(Point2D(x=float(x), y=float(y)))
        self._points_pub.publish(msg)
        self._node.get_logger().debug(f"Published {len(points)} perspective points.")

    # --- Private Subscriber Callbacks ---

    def _undistorted_cb(self, msg: Image):
        """Callback for the raw, undistorted image. Converts to CV2 format."""
        try:
            cv_img = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self._facade.undistorted_image_received.emit(cv_img)
        except Exception as e:
            self._node.get_logger().warn(f"Failed undistorted image conversion: {e}")

    def _annotated_cb(self, msg: Image):
        """Callback for the annotated image. Converts to CV2 format."""
        try:
            cv_img = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self._facade.annotated_image_received.emit(cv_img)
        except Exception as e:
            self._node.get_logger().warn(f"Failed annotated image conversion: {e}")

    def _objects_cb(self, msg: ManyDetectedObjects):
        """Callback for detected objects. Forwards the message directly."""
        self._facade.detected_objects_received.emit(msg)

    def _joints_cb(self, msg: JointState):
        """Callback for joint states. Forwards the message directly."""
        self._facade.joint_state_received.emit(msg)
