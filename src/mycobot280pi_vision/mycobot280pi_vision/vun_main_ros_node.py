"""
vision_undistorter_node

This node is responsible for correcting the barrel distortion from a webcam,
so that straight lines in the real world no longer look curved.

Parameters:
1. `camera_info_file` (`string`): The absolute path to the `.yaml` file containing the camera's intrinsic calibration matrix and distortion coefficients.

Subscribers
-----------
1. `/camera/msg_image_raw`
   * Type: sensor_msgs/msg/Image
   * From: vision_usb_cam_node

Publishers
----------
1. `/vision/msg_undistorted_image`
   * Type: sensor_msgs/msg/Image
   * To: vision_perspective_transformer_node, gui_robot_control_node
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import yaml


class VisionUndistorterNode(Node):
    def __init__(self):
        super().__init__('vision_undistorter_node')

        # Declare and get parameter for the camera calibration file
        self.declare_parameter('camera_info_file', '')
        self.camera_info_file = (
            self.get_parameter('camera_info_file')
            .get_parameter_value()
            .string_value
        )

        # Load camera calibration data
        self.camera_matrix, self.dist_coeffs = self.load_camera_info(self.camera_info_file)

        # ROS <-> OpenCV bridge
        self.bridge = CvBridge()

        # Subscriber
        self.image_sub = self.create_subscription(
            Image,
            '/camera/msg_image_raw',
            self.image_callback,
            10
        )

        # Publisher
        self.image_pub = self.create_publisher(
            Image,
            '/vision/msg_undistorted_image',
            10
        )

        if self.camera_matrix is not None and self.dist_coeffs is not None:
            self.get_logger().info("VisionUndistorterNode initialized and ready.")
        else:
            self.get_logger().error("Calibration data missing or invalid. Node will not process images.")

    def load_camera_info(self, file_path):
        """Loads camera calibration data from a YAML file."""
        if not file_path:
            self.get_logger().error('No camera_info_file parameter provided.')
            return None, None

        try:
            with open(file_path, 'r') as file:
                calib_data = yaml.safe_load(file)

            camera_matrix = np.array(calib_data['camera_matrix']['data']).reshape(3, 3)
            dist_coeffs = np.array(calib_data['distortion_coefficients']['data'])

            self.get_logger().info('Successfully loaded calibration data.')
            return camera_matrix, dist_coeffs

        except Exception as e:
            self.get_logger().error(f'Failed to load camera info: {e}')
            return None, None

    def image_callback(self, msg):
        """Processes each raw image, applies undistortion, and publishes to `/vision/msg_undistorted_image`."""
        if self.camera_matrix is None or self.dist_coeffs is None:
            self.get_logger().warn("Calibration data not loaded, skipping frame.")
            return

        # Convert ROS2 to OpenCV
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        # Undistort
        undistorted = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs)

        # Convert OpenCV to ROS2
        undistorted_msg = self.bridge.cv2_to_imgmsg(undistorted, encoding="bgr8")
        undistorted_msg.header = msg.header  # Preserve timestamp and frame ID

        # Publish
        self.image_pub.publish(undistorted_msg)


def main(args=None):
    rclpy.init(args=args)
    node = VisionUndistorterNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

