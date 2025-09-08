"""
vision_undistorter_node.py

This node is responsible for correcting the barrel distortion from a webcam,
so that straight lines in the real world no longer look curved.


Subscribers

1. `/camera/image_raw` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_usb_cam_node`.
     
Publishers

1. `/vision/undistorted_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_perspective_transformer_node` and `gui_robot_control_node`.

"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import yaml


def __init__(self):
    super().__init__('vision_undistorter_node')

    # Declare and get the parameter for the camera calibration file
    self.declare_parameter('camera_info_file', '')
    self.camera_info_file = self.get_parameter('camera_info_file').get_parameter_value().string_value

    # Load camera calibration data (intrinsic matrix and distortion coefficients)
    self.camera_matrix, self.dist_coeffs = self.load_camera_info(self.camera_info_file)

    # Set up the ROS image bridge (for converting between ROS and OpenCV images)
    self.bridge = CvBridge()

    # Subscribe to the raw camera image topic
    self.image_sub = self.create_subscription(
        Image,
        '/camera/image_raw',
        self.image_callback,
        10
    )

    # Publisher for the undistorted image
    self.image_pub = self.create_publisher(
        Image,
        '/camera/image_undistorted',
        10
    )

    if self.camera_matrix is not None and self.dist_coeffs is not None:
        self.get_logger().info("VisionUndistorterNode initialized and ready.")
    else:
        self.get_logger().error("Calibration data missing or invalid. Node will not process images.")

def load_camera_info(self, file_path):
    """
    Loads camera calibration data from a YAML file.
    Calibration data is required to correct lens distortion.

    Args:
        file_path (str): Path to the calibration YAML file.

    Returns:
        tuple: (camera_matrix, dist_coeffs) if successful, (None, None) otherwise.
    """
    if not file_path:
        self.get_logger().error('No camera_info_file parameter provided.')
        return None, None

    try:
        with open(file_path, 'r') as file:
            calib_data = yaml.safe_load(file)

        # Extract the camera matrix and distortion coefficients from the YAML data
        camera_matrix = np.array(calib_data['camera_matrix']['data']).reshape(3, 3)
        dist_coeffs = np.array(calib_data['distortion_coefficients']['data'])

        self.get_logger().info('Successfully loaded calibration data.')
        return camera_matrix, dist_coeffs

    except Exception as e:
        self.get_logger().error(f'Failed to load camera info: {e}')
        return None, None

def image_callback(self, msg):
    """
    Callback function that processes each incoming raw image.

    Steps:
    1. Converts the ROS image message to an OpenCV image.
    2. Applies lens distortion correction using calibration data.
    3. Converts the corrected image back to a ROS message.
    4. Publishes the undistorted image.

    Args:
        msg (sensor_msgs.msg.Image): The incoming raw image message.
    """
    # If calibration data is missing, skip processing
    if self.camera_matrix is None or self.dist_coeffs is None:
        self.get_logger().warn("Calibration data not loaded, skipping frame.")
        return

    # Convert the ROS image to an OpenCV image (numpy array)
    frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    # Apply the undistortion transformation
    undistorted = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs)

    # Convert the undistorted OpenCV image back to a ROS image message
    undistorted_msg = self.bridge.cv2_to_imgmsg(undistorted, encoding="bgr8")
    undistorted_msg.header = msg.header  # Preserve the original timestamp and frame ID

    # Publish the undistorted image
    self.image_pub.publish(undistorted_msg)
