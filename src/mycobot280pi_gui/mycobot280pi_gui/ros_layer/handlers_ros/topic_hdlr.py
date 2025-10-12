"""
topic_hdlr.py - Defines the TopicHandler.

This class encapsulates all logic for ROS 2 topic communication, including
all publishers and subscribers for the application.
"""

import rclpy.node
from PyQt5.QtCore import QObject
from cv_bridge import CvBridge
import numpy as np

# Import all required message types
from sensor_msgs.msg import Image
from mycobot280pi_interfaces.msg import Point2D, Point2DArray, ManyDetectedObjects, JointAnglesArray

# Constants for topic names
TOPIC_UNDISTORTED_IMAGE = '/vision/msg_undistorted_image'
TOPIC_DETECTED_OBJECTS = '/vision/msg_detected_objects'
TOPIC_ANNOTATED_IMAGE = '/vision/msg_annotated_image'
TOPIC_JOINT_ANGLES = '/robot/msg_joint_angles'
TOPIC_FOUR_POINTS = '/gui/msg_four_perspective_points'

class TopicHandler:
    """Manages all publishers and subscribers for the node."""

    def __init__(self, node, facade):
        # (node: rclpy.node.Node, facade: QObject) -> None
        self._node = node
        self._facade = facade
        self._bridge = CvBridge()
        
        # Publishers
        self._points_pub = self._node.create_publisher(Point2DArray, TOPIC_FOUR_POINTS, 10)
        
        # Subscribers
        self._node.create_subscription(Image, TOPIC_UNDISTORTED_IMAGE, self._undistorted_cb, 10)
        self._node.create_subscription(Image, TOPIC_ANNOTATED_IMAGE, self._annotated_cb, 10)
        self._node.create_subscription(ManyDetectedObjects, TOPIC_DETECTED_OBJECTS, self._objects_cb, 10)
        self._node.create_subscription(JointAnglesArray, TOPIC_JOINT_ANGLES, self._joints_cb, 10)

    def publish_perspective_points(self, points): # (points: np.ndarray) -> None
        msg = Point2DArray()
        for x, y in points:
            msg.points.append(Point2D(x=float(x), y=float(y)))
        self._points_pub.publish(msg)

    def _undistorted_cb(self, msg): # (msg: Image) -> None
        try:
            cv_img = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self._facade.undistorted_image_received.emit(cv_img)
        except Exception as e:
            self._node.get_logger().warn(f"Failed undistorted image conversion: {e}")

    def _annotated_cb(self, msg): # (msg: Image) -> None
        try:
            cv_img = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self._facade.annotated_image_received.emit(cv_img)
        except Exception as e:
            self._node.get_logger().warn(f"Failed annotated image conversion: {e}")

    def _objects_cb(self, msg): # (msg: ManyDetectedObjects) -> None
        self._facade.detected_objects_received.emit(msg)

    def _joints_cb(self, msg): # (msg: JointAnglesArray) -> None
        self._facade.joint_angles_received.emit(msg)
