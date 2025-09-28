import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Image
from std_msgs.msg import Int32MultiArray
from cv_bridge import CvBridge
import cv2
import sys
import numpy as np

class ParamImagePublisher(Node):
    def __init__(self):
        super().__init__('dummy_image_publisher')

        # Declare parameters for both the image path and the object coordinates
        self.declare_parameter('image_path', '')
        self.declare_parameter('object_coords', [])

        # Get the value of the 'image_path' parameter
        image_path_param = self.get_parameter('image_path').get_parameter_value()
        self.image_path = image_path_param.string_value
        
        # Get the value of the 'object_coords' parameter
        object_coords_param = self.get_parameter('object_coords').get_parameter_value()
        self.object_coords = object_coords_param.integer_array_value
        
        # Check if the image path was provided and if the file exists
        if not self.image_path or not cv2.imread(self.image_path) is None:
            self.get_logger().info(f'Image file found at {self.image_path}')
        else:
            self.get_logger().error(f'Could not read image file at {self.image_path}. Please check the path.')
            sys.exit(1)

        # Publisher for the Image topic
        self.image_pub = self.create_publisher(Image, 'detected_objects', 10)
        
        # Publisher for the detected objects topic
        self.objects_pub = self.create_publisher(Int32MultiArray, 'vis', 10)

        self.bridge = CvBridge()
        
        self.timer = self.create_timer(1.0, self.publish_image_and_objects)

    def publish_image_and_objects(self):
        # Read the image from disk
        cv_image = cv2.imread(self.image_path)

        # Draw the bounding box of the dummy object on the image
        if self.object_coords:
            try:
                # The object_coords parameter is a list of integers [x, y, w, h]
                x, y, w, h = self.object_coords
                cv2.rectangle(cv_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(cv_image, f"({x},{y})", (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            except ValueError:
                self.get_logger().warn("Invalid 'object_coords' parameter. Expected a list of 4 integers.")
        
        # Publish the image message
        ros_image_message = self.bridge.cv2_to_imgmsg(cv_image, encoding="bgr8")
        ros_image_message.header.stamp = self.get_clock().now().to_msg()
        self.image_pub.publish(ros_image_message)

        # Publish the object coordinates
        if self.object_coords:
            objects_msg = Int32MultiArray(data=self.object_coords)
            self.objects_pub.publish(objects_msg)
            
        self.get_logger().info('Published image and object coordinates.')


def main(args=None):
    rclpy.init(args=args)
    node = ParamImagePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
