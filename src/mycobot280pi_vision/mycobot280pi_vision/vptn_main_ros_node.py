"""
vision_perspective_transform_node

This ROS2 node listens for undistorted images of the robot's workspace and the four perspective points provided by the GUI
transforms the undistorted image to a top-down "bird's-eye view", and then publishes the image.
If automatic detection fails, it allows the user to manually select the four corners.

 Subscriber 1: 
- Topic: `/vision/msg_undistorted_image`
- Type: `sensor_msgs/msg/Image` 
- Description:   Receives the undistorted image stream from `vision_undistorter_node`.

 Subscriber 2: 
- Topic: `/gui/msg_four_perspective_points`
- Type:  `mycobot280pi_interfaces/msg/Point2DArray`
- Description:  Receives an array of four coordinate points from `gui_robot_control_node` to define the perspective transformation.  

 Publisher:  
- Topic:   `/vision/msg_top_down_image`
- Type:   `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
- Description:   Publishes the resulting top-down image to `vision_object_detector_node` and `gui_robot_control_node`.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
import threading

# Import the perspective transform helper (now encapsulates ordering + warp)
from mycobot280pi_vision.vptn_perspective_transform import compute_topdown

# Custom Interfaces
from mycobot280pi_interfaces.msg import Point2DArray  

class VisionPerspectiveTransformNode(Node):
    """Transforms an incoming undistorted perspective image into a square top-down view.

    Responsibilities:
    - Subscribe to `/vision/msg_undistorted_image` (sensor_msgs/Image).
    - Subscribe to `/gui/msg_four_perspective_points` (Point2DArray) supplied by the GUI.
    - When BOTH an image and 4 valid points are present, compute perspective warp.
    - Publish warped image on `/vision/msg_top_down_image` (sensor_msgs/Image).

    Notes / Project Conventions:
    - GUI sends points in image pixel coordinates.
    - Order of points from GUI may be arbitrary (user drags) → we must order them deterministically.
    - Existing warp_perspective() expects source points ordered to map to destination order:
        dst = [TR, TL, BL, BR] (non‑standard ordering defined in vptn_perspective_transform.py)
    - We therefore build (TR, TL, BL, BR) when calling warp_perspective.
    """

    def __init__(self):
        super().__init__('vision_perspective_transform_node')
        self.bridge = CvBridge()

        # Parameters
        self.declare_parameter('output_size', 600)
        self.output_size = int(self.get_parameter('output_size').value)

        # Internal state
        self._latest_image = None          # (cv_image, header)
        self._latest_points = None         # np.ndarray shape (4,2)
        self._lock = threading.Lock()
        self._last_warn_missing_points = 0.0

        # Subscriptions
        self.create_subscription(
            Image,
            '/vision/msg_undistorted_image',
            self.image_callback,
            10
        )
        self.create_subscription(
            Point2DArray,
            '/gui/msg_four_perspective_points',
            self.perspective_points_callback,
            10
        )

        # Publisher
        self.topdown_pub = self.create_publisher(
            Image,
            '/vision/msg_top_down_image',
            10
        )

        self.get_logger().info("vision_perspective_transform_node is ready (waiting for image + 4 points)")

    def _try_publish_warp(self):
        """Attempt warp & publish if both image and 4 points available."""
        with self._lock:
            if self._latest_image is None or self._latest_points is None:
                return
            cv_image, header = self._latest_image
            pts = self._latest_points

        if pts.shape != (4, 2):
            self.get_logger().warn(f"Expected 4 points, got shape {pts.shape}; skipping warp")
            return

        try:
            warped = compute_topdown(cv_image, pts, output_size=self.output_size)
        except Exception as e:
            self.get_logger().error(f"Perspective warp failed: {e}")
            return

        try:
            out_msg = self.bridge.cv2_to_imgmsg(warped, encoding='bgr8')
            # Preserve timing metadata; keep same frame_id for traceability
            out_msg.header = header
            out_msg.header.frame_id = header.frame_id or 'vision_topdown'
            self.topdown_pub.publish(out_msg)
        except Exception as e:
            self.get_logger().error(f"Failed to publish warped image: {e}")

    # ----------------------------- Callbacks ---------------------------------------
    def image_callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Failed to convert incoming image: {e}")
            return
        with self._lock:
            self._latest_image = (cv_image, msg.header)
        self._try_publish_warp()

    def perspective_points_callback(self, msg: Point2DArray):
        # Extract points
        pts_list = [(p.x, p.y) for p in msg.points]
        if len(pts_list) != 4:
            # Throttle warning to avoid spamming logs if GUI still dragging points
            now = self.get_clock().now().seconds_nanoseconds()[0]
            if now - self._last_warn_missing_points > 1.0:
                self.get_logger().warn(f"Need exactly 4 points; received {len(pts_list)}. Waiting...")
                self._last_warn_missing_points = now
            return
        pts = np.array(pts_list, dtype=np.float32)
        with self._lock:
            self._latest_points = pts
        self._try_publish_warp()


def main(args=None):
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
