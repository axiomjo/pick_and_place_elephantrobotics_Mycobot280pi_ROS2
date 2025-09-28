import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import time

class RawImagePublisher(Node):
    def __init__(self):
        super().__init__('dummy_undistorted_image_publisher')
        self.br = CvBridge()
        
        # Publisher for the raw image stream
        self.image_pub = self.create_publisher(Image, '/dummy/undistorted600x600', 10)
        
        # Create a timer to publish at a fixed rate (e.g., 30 Hz)
        self.timer = self.create_timer(1.0 / 30.0, self.publish_dummy_grid_image)

    def publish_dummy_grid_image(self):
        image_width, image_height = 600, 600
        dummy_image = np.zeros((image_height, image_width, 3), dtype=np.uint8)

        # Draw a simple grid pattern
        grid_color = (200, 200, 200)
        step = 50
        for i in range(0, image_width, step):
            cv2.line(dummy_image, (i, 0), (i, image_height), grid_color, 1)
        for i in range(0, image_height, step):
            cv2.line(dummy_image, (0, i), (image_width, i), grid_color, 1)
            
        # Calculate the center coordinates
        center_x = image_width // 2
        center_y = image_height // 2
        center_coordinates = (center_x, center_y)

        # Set the radius and color for the red dot
        radius = 5  # You can adjust the size of the dot
        red_color = (0, 0, 255) # BGR format for red

        # Draw the red circle on the image
        cv2.circle(dummy_image, center_coordinates, radius, red_color, -1)

        # Draw colored squares at specific intersections
        square_size = 20
        # Red square at (150, 150)
        cv2.rectangle(dummy_image, (150 - square_size // 2, 150 - square_size // 2),
                      (150 + square_size // 2, 150 + square_size // 2), (0, 0, 255), -1)
        # Green square at (450, 300)
        cv2.rectangle(dummy_image, (450 - square_size // 2, 300 - square_size // 2),
                      (450 + square_size // 2, 300 + square_size // 2), (0, 255, 0), -1)
        # Blue square at (300, 450)
        cv2.rectangle(dummy_image, (300 - square_size // 2, 450 - square_size // 2),
                      (300 + square_size // 2, 450 + square_size // 2), (255, 0, 0), -1)
        
        # Publish the dummy image
        ros_image_msg = self.br.cv2_to_imgmsg(dummy_image, "bgr8")
        ros_image_msg.header.stamp = self.get_clock().now().to_msg()
        self.image_pub.publish(ros_image_msg)
        
        self.get_logger().info('Published dummy grid image with colored squares.')
def main(args=None):
    rclpy.init(args=args)
    node = RawImagePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
