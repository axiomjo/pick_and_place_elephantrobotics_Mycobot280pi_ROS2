import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor 
from rclpy.callback_groups import ReentrantCallbackGroup

from .prn_planning_logic import PlannerLogicActionClient
from .prn_action_server_complex_command import ComplexCommandActionServer

class PlannerRobotNode(Node):
    def __init__(self):
        super().__init__('planner_robot_node')
        
        # Create ReentrantCallbackGroups for parallel processing
        action_callback_group = ReentrantCallbackGroup()
        logic_client_callback_group = ReentrantCallbackGroup() 

        self.logic = PlannerLogicActionClient(self, logic_client_callback_group) 
        self.action_server = ComplexCommandActionServer(self, self.logic, action_callback_group)

        self.get_logger().info("PlannerRobotNode is up and running. 🧠")
        
def main(args=None):
    rclpy.init(args=args)
    node = PlannerRobotNode()
    
    # Use MultiThreadedExecutor to handle the action server and action client 
    # callbacks concurrently. This is essential for the blocking sequence.
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
