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
import numpy as np
from cv_bridge import CvBridge

# ROS 2 Message Imports
from sensor_msgs.msg import Image
from mycobot280pi_interfaces.msg import Point2DArray

# Import the logic class from the other file
from .vptn_perspective_transform import PerspectiveTransformer

class VisionPerspectiveTransformNode(Node):
    """
    A ROS 2 node that subscribes to an image and four points, performs a 
    perspective transform, and publishes the resulting top-down image.
    """

    def __init__(self):
        super().__init__('vision_perspective_transformer_node')
        self.get_logger().info('Perspective Transformer Node has started.')

        # State variables to hold the latest data from subscribers
        self.latest_image = None
        self.latest_points = None

        # Initialize the CvBridge and the transformer logic
        self.bridge = CvBridge()
        self.transformer = PerspectiveTransformer()

         # === SUBSCRIBERS ===
        self.image_subscriber = self.create_subscription(
            Image,
            '/vision/msg_undistorted_image',
            self.image_callback,
            10
        )
        
        self.points_subscriber = self.create_subscription(
            Point2DArray,
            '/gui/msg_four_perspective_points',
            self.points_callback,
            10
        )

        # === PUBLISHER ===
        self.top_down_publisher = self.create_publisher(
            Image,
            '/vision/msg_top_down_image',
            10
        )
        
    def image_callback(self, msg: Image):
        """Callback for the undistorted image topic."""
        try:
            self.latest_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            self.process_and_publish()
        except Exception as e:
            self.get_logger().error(f'Failed to convert image: {e}')

    def points_callback(self, msg: Point2DArray):
        """Callback for the four points topic from the GUI."""
        if len(msg.points) == 4:
            # Convert the message to a NumPy array of shape (4, 2)
            self.latest_points = np.array(
                [[p.x, p.y] for p in msg.points], 
                dtype=np.float32
            )
            self.process_and_publish()
        else:
            self.get_logger().warn(
                f'Received points message with {len(msg.points)} points, expected 4.')
            self.latest_points = None
        

    def process_and_publish(self):
        """
        Checks if all required data is available and, if so,
        performs the transformation and publishes the result.
        """
        # Only proceed if we have received at least one image and one set of valid points
        if self.latest_image is None or self.latest_points is None:
            return

        # Perform the transformation using our logic class
        warped_image = self.transformer.transform(self.latest_image, self.latest_points)

        if warped_image is not None:
            try:
                # Convert the warped OpenCV image back to a ROS message and publish
                top_down_msg = self.bridge.cv2_to_imgmsg(warped_image, 'bgr8')
                self.top_down_publisher.publish(top_down_msg)
            except Exception as e:
                self.get_logger().error(f'Failed to publish warped image: {e}')


def main(args=None):
    rclpy.init(args=args)
    vptn_node = VisionPerspectiveTransformNode()
    rclpy.spin(vptn_node)
    
    # Cleanup
    vptn_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

        
        
        
        
        
        
