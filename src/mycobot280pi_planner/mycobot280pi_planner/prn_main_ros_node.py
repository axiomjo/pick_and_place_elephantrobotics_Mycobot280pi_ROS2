# prn_main_ros_node.py

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup

from .prn_robot_commander import RobotCommander # NEW
from .prn_planning_logic import PlannerLogic
from .prn_action_server import PlannerActionServer
from .prn_service_server import PlannerServiceServer

class PlannerRobotNode(Node):
    def __init__(self):
        super().__init__('planner_robot_node')
        
        # Callback groups for concurrency
        action_callback_group = ReentrantCallbackGroup()
        feedback_callback_group = ReentrantCallbackGroup()

        # 1. Build the low-level Robot Commander
        # This component handles all direct communication with the executor.
        commander = RobotCommander(self, feedback_callback_group)

        # 2. Build the high-level Planner Logic
        # It uses the commander to execute its plans.
        self.logic = PlannerLogic(self, commander)

        # 3. Build the communication interfaces (servers)
        # They interact with the high-level logic.
        self.action_server = PlannerActionServer(self, self.logic, action_callback_group)
        self.service_server = PlannerServiceServer(self, self.logic)

        self.get_logger().info("PlannerRobotNode is up and running. 🧠")

def main(args=None):
    rclpy.init(args=args)
    node = PlannerRobotNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
