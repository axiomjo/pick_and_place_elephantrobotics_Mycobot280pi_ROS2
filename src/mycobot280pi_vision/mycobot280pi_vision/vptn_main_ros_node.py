"""
vision_perspective_transform_node.py

This ROS2 node listens for undistorted images of the robot's workspace,
detects the working area (rectangle), and publishes a top-down, "unwarped" view.
If automatic detection fails, it allows the user to manually select the four corners.

Subscribers
1. `/vision/undistorted_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_undistorter_node`.

2. `/vision/perspective_points` Topic
   * **Interface Type:** `mycobot280pi_interfaces/msg/Point2DArray`
   * **Details:** Receives from `gui_robot_control_node`.
     
Publishers
1. `/vision/corrected_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_object_detector_node` and `gui_robot_control_node`.

"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
import threading

# Import the perspective transform functions
from mycobot280pi_vision.vptn_perspective_transform import detect_quadrilateral_corners, warp_perspective

# Custom Interfaces
from mycobot280pi_interfaces.msg import Point2DArray  # Import your custom message

class VisionPerspectiveTransformNode(Node):
    """
    A ROS2 node that transforms a slanted view of the workspace into a top-down view.
    """
    def __init__(self):
        super().__init__('vision_perspective_transform_node')
        self.bridge = CvBridge()

        # Subscribe to the undistorted image topic
        self.create_subscription(
            Image,
            'vision/undistorted_image',
            self.image_callback,
            10
        )

        # Subscribe to perspective points from GUI
        self.create_subscription(
            Point2DArray,
            'vision/perspective_points',
            self.perspective_points_callback,
            10
        )

        # Publisher for the corrected image
        self.topdown_pub = self.create_publisher(
            Image,
            'vision/corrected_image',
            10
        )


        # Store the latest perspective points from GUI
        self.latest_points = None

        self.get_logger().info("VisionPerspectiveTransformNode ready and listening for images and perspective points.")

    def perspective_points_callback(self, msg):
        """
        Callback to receive perspective points from the GUI.
        Stores the points for use in the next image callback.
        """
        # Convert Point2DArray to numpy array of shape (4,2)
        self.latest_points = np.array([[pt.x, pt.y] for pt in msg.points], dtype=np.float32)
        self._status("Received new perspective points from GUI.")

    def image_callback(self, msg):
        """
        Callback for incoming undistorted images.
        Uses GUI points if available, otherwise tries auto-detection.
        """
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self._status("Received undistorted image.")

        # Use GUI-provided points if available and valid
        if self.latest_points is not None and len(self.latest_points) == 4:
            src_pts = self.latest_points
            self._status("Using perspective points from GUI.")
        else:
            src_pts = detect_quadrilateral_corners(frame)
            if src_pts is None or len(src_pts) != 4:
                self._status("Auto corner detection failed. Please select 4 corners manually.")
                src_pts = self._manual_point_selection(frame)
                if src_pts is None:
                    self._status("Manual selection cancelled. Skipping this frame.")
                    return

        # Perform the perspective transform
        warped = warp_perspective(frame, src_pts)
        warped_msg = self.bridge.cv2_to_imgmsg(warped, encoding='bgr8')
        warped_msg.header = msg.header

        self.topdown_pub.publish(warped_msg)
        self._status("Published corrected image to /corrected_image.")


    def _status(self, text):
        """Publish and log status messages."""
        self.get_logger().info(text)
        self.status_pub.publish(String(data=text))

    def _manual_point_selection(self, frame):
        """
        Allows the user to manually select 4 points (corners) on the image.
        Returns the selected points as a numpy array, or None if cancelled.
        """
        self.manual_points = []
        self.manual_done_event.clear()
        clone = frame.copy()

        cv2.namedWindow(self.manual_win)
        cv2.setMouseCallback(self.manual_win, self._manual_click)

        self._status("Click 4 points in order: top-left, top-right, bottom-right, bottom-left.")

        while not self.manual_done_event.is_set():
            disp = clone.copy()
            for i, pt in enumerate(self.manual_points):
                cv2.circle(disp, pt, 5, (0, 255, 0), -1)
                if i > 0:
                    cv2.line(disp, self.manual_points[i-1], pt, (0, 255, 0), 2)
            if len(self.manual_points) == 4:
                cv2.line(disp, self.manual_points[3], self.manual_points[0], (0, 255, 0), 2)
            cv2.imshow(self.manual_win, disp)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                cv2.destroyWindow(self.manual_win)
                return None

        src_pts = np.float32(self.manual_points)
        cv2.destroyWindow(self.manual_win)
        return src_pts

    def _manual_click(self, event, x, y, flags, param):
        """
        Mouse callback for manual point selection.
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.manual_points) < 4:
                self.manual_points.append((x, y))
            if len(self.manual_points) == 4:
                self.manual_done_event.set()

def main(args=None):
    """
    Main entry point for the node.
    """
    rclpy.init(args=args)
    node = VisionPerspectiveTransformNode()
    try:
        rclpy.spin(node)
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
