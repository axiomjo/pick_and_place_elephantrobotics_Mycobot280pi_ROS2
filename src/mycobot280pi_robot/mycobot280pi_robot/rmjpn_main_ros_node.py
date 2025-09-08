"""
robot_mycobot_joint_publisher_node

This node runs on the MyCobot 280 Pi and continuously reads the robot's joint angles using the pymycobot API.
It publishes the robot's joint states to the `/robot/joint_states` topic, so other nodes (like the GUI or RViz)
can visualize and monitor the robot's current pose.

[8 Sep]
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header

import pymycobot
from pymycobot import MyCobot, PI_PORT, PI_BAUD

class RobotMycobotJointPublisherNode(Node):
    """
    Publishes the MyCobot's joint angles (in radians) to /robot/joint_states at 30 Hz.
    """
    def __init__(self):
        super().__init__("robot_mycobot_joint_publisher_node")

        # Try to connect to the MyCobot hardware
        try:
            self.get_logger().info(f"Connecting to MyCobot on port: {PI_PORT}, baud: {PI_BAUD}")
            self.mc = MyCobot(PI_PORT, PI_BAUD)
        except Exception as e:
            self.get_logger().error(f"Failed to connect to MyCobot: {e}")
            raise

        # Publisher for joint states (matches README: /robot/joint_states)
        self.publisher = self.create_publisher(
            JointState,
            "/robot/joint_states",
            qos_profile=10
        )

        # The names of the robot's joints (order matters)
        self.joint_names = [
            "joint2_to_joint1",
            "joint3_to_joint2",
            "joint4_to_joint3",
            "joint5_to_joint4",
            "joint6_to_joint5",
            "joint6output_to_joint6",
        ]

        # Publish at 30 Hz
        timer_period = 1.0 / 30.0
        self.timer = self.create_timer(timer_period, self.publish_joint_states)
        self.get_logger().info("robot_mycobot_joint_publisher_node is running and publishing joint states.")

    def publish_joint_states(self):
        """
        Reads the current joint angles from the robot, converts them to radians,
        and publishes them as a JointState message.
        """
        try:
            # Get joint angles in degrees from the robot
            res = self.mc.get_angles()
            if not res or len(res) != 6 or all(angle == 0.0 for angle in res):
                self.get_logger().warn("Invalid joint angles received. Skipping this cycle.")
                return

            # Convert angles to radians for ROS compatibility
            radians_list = [math.radians(angle) for angle in res]

            # Create and fill the JointState message
            joint_state_msg = JointState()
            joint_state_msg.header = Header()
            joint_state_msg.header.stamp = self.get_clock().now().to_msg()
            joint_state_msg.name = self.joint_names
            joint_state_msg.position = radians_list
            joint_state_msg.velocity = []
            joint_state_msg.effort = []

            # Publish the message
            self.publisher.publish(joint_state_msg)
            self.get_logger().debug(f"Published joint states: {radians_list}")

        except Exception as e:
            self.get_logger().error(f"Error while publishing joint states: {e}")

def main(args=None):
    """
    Main entry point for the node.
    Initializes ROS, creates the node, and spins.
    """
    rclpy.init(args=args)
    node = RobotMycobotJointPublisherNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
