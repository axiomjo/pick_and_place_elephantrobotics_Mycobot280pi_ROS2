# prn_action_client_command_primitives.py
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from mycobot280pi_interfaces.action import SimpleCommandsAction
from rclpy.callback_groups import CallbackGroup

# This is the action name from your original file
ACTION_COMMAND_PRIMITIVES = '/planner/act_command_primitives'

class CommandPrimitivesActionClient:
    """
    A SYNCHRONOUS, blocking wrapper for the SimpleCommandsAction client.
    """
    def __init__(self, node: Node, callback_group: CallbackGroup):
        self.node = node
        self.logger = node.get_logger()
        
        self.action_client = ActionClient(
            node,
            SimpleCommandsAction,
            ACTION_COMMAND_PRIMITIVES,
            callback_group=callback_group
        )
        
        if not self.action_client.wait_for_server(timeout_sec=5.0):
            self.logger.error(f"Action server '{ACTION_COMMAND_PRIMITIVES}' not available! Shutting down.")
            raise SystemExit(f"Action server '{ACTION_COMMAND_PRIMITIVES}' not available")
        
        self.logger.info(f"Action server '{ACTION_COMMAND_PRIMITIVES}' is ready.")

    def send_goal(self, cmd_goal: SimpleCommandsAction.Goal):
        """
        Sends a goal and blocks until the goal is complete.
        Returns: (success: bool, message: str, goal_handle)
        """
        self.logger.info(f"Sending sync goal: {cmd_goal.command_type}")
        
        # 1. Send the goal and wait for it to be accepted
        send_goal_future = self.action_client.send_goal_async(cmd_goal)
        
        # This spins the node just enough to complete this future
        rclpy.spin_until_future_complete(self.node, send_goal_future)
        
        goal_handle = send_goal_future.result()
        if not goal_handle.accepted:
            self.logger.warn(f"Simple command '{cmd_goal.command_type}' was REJECTED.")
            return False, "Goal was rejected", None
            
        self.logger.info(f"Simple command '{cmd_goal.command_type}' was ACCEPTED.")

        # 2. Wait for the goal to be finished
        get_result_future = goal_handle.get_result_async()
        
        # This spins the node just enough to get the result
        rclpy.spin_until_future_complete(self.node, get_result_future)
        
        result_wrapper = get_result_future.result()
        result = result_wrapper.result
        
        if not result.success:
            self.logger.warn(f"Simple command FAILED: {result.message}")
            return False, result.message, goal_handle
            
        self.logger.info(f"Simple command SUCCEEDED: {result.message}")
        return True, result.message, goal_handle
