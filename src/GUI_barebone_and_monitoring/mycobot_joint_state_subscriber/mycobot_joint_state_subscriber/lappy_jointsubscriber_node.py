import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState # Import the message type for JointState

class JointStateListener(Node):
    """
    A simple ROS 2 node that subscribes to 'joint_states' and prints the received data.
    """
    def __init__(self):
        super().__init__("mycobot_joint_subscriber_node_di_rasppi") 
        self.get_logger().info("JointStateListener Node: Initializing...")

        # Create a subscription to the 'joint_states' topic
        # When a message arrives, the 'joint_callback' method will be called.
        self.subscription = self.create_subscription(
            msg_type=JointState,
            topic="joint_states",
            callback=self.joint_callback,
            qos_profile=10 # Quality of Service profile (standard for real-time data)
        )
        self.get_logger().info("JointStateListener Node: Subscribing to topic: /joint_states")

    def joint_callback(self, msg: JointState):
        """
        Callback function for the JointState subscriber.
        This function is executed every time a JointState message is received.
        """
        self.get_logger().info(f"Received JointState at stamp: {msg.header.stamp.sec}.{msg.header.stamp.nanosec}")
        self.get_logger().info(f"  Joint Names: {msg.name}")
        self.get_logger().info(f"  Joint Positions (radians): {[f'{p:.4f}' for p in msg.position]}")
        # You can add more processing or even convert to degrees here if needed:
        # degrees = [round(p * 180.0 / 3.14159, 1) for p in msg.position]
        # self.get_logger().info(f"  Joint Positions (degrees): {degrees}")


def main(args=None):
    """
    Main function to initialize ROS 2 and run the node.
    """
    rclpy.init(args=args) # Initialize the ROS 2 client library
    node = JointStateListener() # Create an instance of our node

    try:
        rclpy.spin(node) # Keep the node alive and process callbacks until shutdown
    except KeyboardInterrupt:
        node.get_logger().info("JointStateListener Node: KeyboardInterrupt caught, shutting down.")
    finally:
        node.destroy_node() # Clean up the node resources
        rclpy.shutdown() # Shut down the ROS 2 client library

if __name__ == "__main__":
    main()
