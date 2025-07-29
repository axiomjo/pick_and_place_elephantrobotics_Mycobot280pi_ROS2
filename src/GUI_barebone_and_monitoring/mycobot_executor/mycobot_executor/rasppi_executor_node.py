import rclpy
from rclpy.node import Node
from mycobot_interfaces.msg import MycobotCoords
from sensor_msgs.msg import JointState

from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD

import math
import time

class MyCobotExecutor(Node):
    def __init__(self):
        super().__init__('mycobot_executor_node')

        # Adjust the port as needed
        self.mc = MyCobot(PI_PORT, PI_BAUD)
        
        # Create subscriber for pose goals
        self.pose_sub = self.create_subscription(
            MycobotCoords,
            'mycobot_280pi_29jul/pose_goal',
            self.pose_callback,
            10
        )

        # Create joint state publisher for GUI feedback
        self.joint_pub = self.create_publisher(JointState, 'joint_states', 10)
        self.create_timer(1.0, self.publish_joint_states)  # every 1s

        self.get_logger().info("MyCobot Executor Node is ready.")

    def pose_callback(self, msg):
        coords = [msg.x, msg.y, msg.z, msg.rx, msg.ry, msg.rz]
        self.get_logger().info(f"Received pose: {coords}")

        # Send to robot (speed: 50, mode: 1 = linear)
        try:
            self.mc.send_coords(coords, 50, 1)
        except Exception as e:
            self.get_logger().error(f"Failed to send coords: {e}")

    def publish_joint_states(self):
        try:
            angles = self.mc.get_angles()  # returns list of 6 floats in degrees
            if angles and len(angles) == 6:
                js_msg = JointState()
                js_msg.name = [f'joint{i+1}' for i in range(6)]
                js_msg.position = [math.radians(a) for a in angles]  # convert to radians
                js_msg.header.stamp = self.get_clock().now().to_msg()
                self.joint_pub.publish(js_msg)
        except Exception as e:
            self.get_logger().warn(f"Could not read joint angles: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = MyCobotExecutor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

