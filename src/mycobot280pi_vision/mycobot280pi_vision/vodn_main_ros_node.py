"""
vodn_main_ros_node.py

Main ROS2 node for vision_object_detector_node.
Subscribes to /vision/corrected_image, runs object detection, and publishes results to /vision/detected_objects.
"""

import rclpy
from rclpy.node import Node

import cv2
from cv_bridge import CvBridge

from .vodn_object_detection import detect_objects, draw_detections

from mycobot280pi_interfaces.msg import ManyDetectedObjects, OneDetectedObject, Point2D
from sensor_msgs.msg import Image
from std_msgs.msg import Header


def objects_to_rosmsg(detected_objects, header: Header):
    """
    Converts a list of detected objects to a ManyDetectedObjects ROS message.

    Args:
        detected_objects (List[dict]): List of dicts with keys id, x, y, w, h.
        header (std_msgs.msg.Header): Header from the input image.

    Returns:
        ManyDetectedObjects: ROS message containing all detected objects. already cleaned so it gives center points. but, still uses computer graphics coordinate.
    """
    msg = ManyDetectedObjects()
    msg.header = header
    for obj in detected_objects:
        one = OneDetectedObject()
        one.id = obj['id']
        # Center point calculation
        center = Point2D()
        center.x = float(obj['x'] + obj['w'] // 2)
        center.y = float(obj['y'] + obj['h'] // 2)
        one.center_point = center
        one.width = obj['w']
        one.height = obj['h']

        msg.objects.append(one)
        
    return msg



class VisionObjectDetectorNode(Node):
    def __init__(self):
        super().__init__('vision_object_detector_node')
        self.bridge = CvBridge()
        
        self.last_process_time = 0
        self.process_interval = 1.0 # 1 Hz
        

        # Subscribe to the corrected image topic
        self.image_sub = self.create_subscription(
            Image,
            '/vision/msg_top_down_image',
            self.image_callback,
            10
        )

        # Publisher for detected objects
        self.objects_pub = self.create_publisher(
            ManyDetectedObjects,
            '/vision/msg_detected_objects',
            10
        )
        
        # Publisher for annotated image
        self.annotated_image_pub = self.create_publisher(
            Image,
            '/vision/msg_annotated_image',
            10
        )

        self.get_logger().info("vision_object_detector_node started.")

    def image_callback(self, msg):
        
        # non-blocking timer kyk dulu pak andri
        current_time = self.get_clock().now().nanoseconds / 1e9
        if (current_time - self.last_process_time) < self.process_interval:
            return # Skip this frame
        self.last_process_time = current_time


        # Convert ROS image to OpenCV image
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'Failed to convert image: {e}')
            return
            
        # Detect objects (returns a list of bounding boxes)
        detected_objects = detect_objects(cv_image)
        
        # draw bounding boxes
        annotated_image = draw_detections(cv_image, detected_objects)

        # Convert to ROS message
        detected_objects_msg = objects_to_rosmsg(detected_objects, msg.header)
        annotated_image_msg = self.bridge.cv2_to_imgmsg(annotated_image, "bgr8")

        # Publish detected objects
        self.objects_pub.publish(detected_objects_msg)
        self.annotated_image_pub.publish(annotated_image_msg)

def main(args=None):
    rclpy.init(args=args)
    node = VisionObjectDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
