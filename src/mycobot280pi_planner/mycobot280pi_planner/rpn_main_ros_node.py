"""
rpn_main_ros_node.py

Main ROS2 node for planner_robot_node.
Initializes the planner logic, action server, and service server.
Handles communication between the GUI, vision, and executor nodes.
"""

import rclpy
from rclpy.node import Node
from mycobot280pi_interfaces.msg import ManyDetectedObjects, SimpleCommands
from mycobot280pi_interfaces.srv import Mycobot280PiSetCoordsMadeSure
from mycobot280pi_interfaces.action import ProcessWorkspace

from .rpn_planning_logic import PlannerLogic
from .rpn_action_server import PlannerActionServer
from .rpn_service_server import PlannerServiceServer

class PlannerRobotNode(Node):
    def __init__(self):
        super().__init__('planner_robot_node')
        self.logic = PlannerLogic(self)
        self.action_server = PlannerActionServer(self, self.logic)
        self.service_server = PlannerServiceServer(self, self.logic)

        # Subscribe to detected objects (from vision pipeline)
        self.create_subscription(
            ManyDetectedObjects,
            '/vision/detected_objects',
            self.logic.detected_objects_callback,
            10
        )

        # Subscribe to manual commands (from GUI)
        self.create_subscription(
            SimpleCommands,
            '/planner/manual_commands',
            self.logic.manual_command_callback,
            10
        )

        # Publisher for atomic commands (to executor)
        self.command_pub = self.create_publisher(
            SimpleCommands,
            '/planner/commands',
            10
        )
        self.logic.set_command_publisher(self.command_pub)

        self.get_logger().info("planner_robot_node is up and running.")

def main(args=None):
    rclpy.init(args=args)
    node = PlannerRobotNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
