"""
vodn_main_ros_node.py

Main ROS2 node for vision_object_detector_node.
Subscribes to /vision/corrected_image, runs object detection, and publishes results to /vision/detected_objects.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from mycobot280pi_interfaces.msg import ManyDetectedObjects
from cv_bridge import CvBridge

from mycobot280pi_vision.vodn_object_detection import detect_objects
from mycobot280pi_vision.vodn_message_converter import objects_to_rosmsg

class VisionObjectDetectorNode(Node):
    """
    The Finder: Detects objects in the corrected image and publishes results.
    """
    def __init__(self):
        super().__init__('vision_object_detector_node')
        self.bridge = CvBridge()

        # Subscribe to the corrected image topic
        self.create_subscription(
            Image,
            '/vision/corrected_image',
            self.image_callback,
            10
        )

        # Publisher for detected objects
        self.objects_pub = self.create_publisher(
            ManyDetectedObjects,
            '/vision/detected_objects',
            10
        )

        self.get_logger().info("vision_object_detector_node started.")

    def image_callback(self, msg):
        # Convert ROS image to OpenCV image
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # Detect objects (returns a list of bounding boxes)
        detected_objects = detect_objects(frame)

        # Convert detection results to ROS message
        rosmsg = objects_to_rosmsg(detected_objects, msg.header)

        # Publish detected objects
        self.objects_pub.publish(rosmsg)

def main(args=None):
    rclpy.init(args=args)
    node = VisionObjectDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
