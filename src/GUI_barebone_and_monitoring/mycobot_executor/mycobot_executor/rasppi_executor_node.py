import rclpy
from rclpy.node import Node
from mycobot_interfaces.msg import MycobotCoords
from sensor_msgs.msg import JointState

from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD

import time

class MyCobotExecutor(Node):
    def __init__(self):
        super().__init__('mycobot_executor_node_di_rasppi')

        # Adjust the port as needed
        self.mc = MyCobot(PI_PORT, PI_BAUD)
        
        # Create subscriber for pose goals
        self.pose_sub = self.create_subscription(
            MycobotCoords,
            'mycobot_280pi_29jul/pose_goal',
            self.pose_callback,
            10
        )

        self.get_logger().info("MyCobot Executor Node is ready. siap nerima perintah dari GUI_node :D")

    def pose_callback(self, msg):
        coords = [msg.x, msg.y, msg.z, msg.rx, msg.ry, msg.rz]
        self.get_logger().info(f"Received pose: {coords}")

        # Send to robot (speed: 50, mode: 1 = linear)
        try:
            self.mc.send_coords(coords, 50, 1)
        except Exception as e:
            self.get_logger().error(f"Failed to send coords: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = MyCobotExecutor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

