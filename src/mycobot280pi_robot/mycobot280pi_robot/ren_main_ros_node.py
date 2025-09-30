"""
ren_main_ros_node.py

Main ROS2 node for robot_mycobot_executor_node.
Listens for atomic robot commands from the planner and executes them using pymycobot.
"""

import rclpy
from rclpy.node import Node
from mycobot280pi_interfaces.msg import SimpleCommands
from .ren_mycobot_interface import MyCobotInterface
from .ren_robot_state_manager import RobotStateManager

class RobotMycobotExecutorNode(Node):
    def __init__(self):
        super().__init__('robot_mycobot_executor_node')
        self.api = MyCobotInterface(self.get_logger())
        self.state_manager = RobotStateManager(self.get_logger())

        # Subscribe to atomic commands from the planner
        self.create_subscription(
            SimpleCommands,
            '/planner/commands',
            self.command_callback,
            10
        )
        self.get_logger().info("robot_mycobot_executor_node is ready and waiting for commands.")

    def command_callback(self, msg: SimpleCommands):
        """
        Receives a SimpleCommands message and executes the requested action.
        """
        try:
            if msg.command_type == "move":
                self.api.move_to_coords(msg.coords, msg.speed)
                self.state_manager.set_state("moving")
            elif msg.command_type == "vacuum_on":
                self.api.vacuum_strong()
                self.state_manager.set_state("vacuum_on")
            elif msg.command_type == "vacuum_off":
                self.api.vacuum_off()
                self.state_manager.set_state("vacuum_off")
            elif msg.command_type == "vacuum_weak":
                self.api.vacuum_weak()
                self.state_manager.set_state("vacuum_weak")
            elif msg.command_type == "set_rgb":
                self.api.set_rgb(msg.r, msg.g, msg.b)
                self.state_manager.set_state("set_rgb")
            else:
                self.get_logger().warn(f"Unknown command_type: {msg.command_type}")
        except Exception as e:
            self.state_manager.set_error(str(e))

def main(args=None):
    rclpy.init(args=args)
    node = RobotMycobotExecutorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
