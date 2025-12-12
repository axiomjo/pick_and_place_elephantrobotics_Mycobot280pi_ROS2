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
    SAFE for MultiThreadedExecutor use.
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
        
        # wait_for_server is safe to call in init usually, but better to use a timeout loop
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
        
        # 1. Send goal asynchronously
        send_goal_future = self.action_client.send_goal_async(cmd_goal)
        
        # 2. BLOCKING WAIT (Safe because of MultiThreadedExecutor)
        try:
            goal_handle = send_goal_future.result()
        except Exception as e:
            self.logger.error(f"Service call failed: {e}")
            return False, f"Service call failed: {e}", None

        # --- FIX START: CRITICAL SAFETY CHECK ---
        # This prevents the "AttributeError: 'NoneType' object has no attribute 'accepted'"
        if goal_handle is None:
            self.logger.error("Goal rejected: ClientGoalHandle is None. Server might be unreachable.")
            return False, "Goal rejected (handle is None)", None
        # --- FIX END ---

        if not goal_handle.accepted:
            self.logger.warn(f"Simple command '{cmd_goal.command_type}' was REJECTED.")
            return False, "Goal was rejected", None
            
        self.logger.info(f"Simple command '{cmd_goal.command_type}' was ACCEPTED.")

        # 3. Request result asynchronously
        get_result_future = goal_handle.get_result_async()
        
        # 4. BLOCKING WAIT again
        try:
            result_wrapper = get_result_future.result()
        except Exception as e:
            self.logger.error(f"Failed to get result: {e}")
            return False, f"Failed to get result: {e}", goal_handle

        result = result_wrapper.result
        
        if not result.success:
            self.logger.warn(f"Simple command FAILED: {result.message}")
            return False, result.message, goal_handle
            
        self.logger.info(f"Simple command SUCCEEDED: {result.message}")
        return True, result.message, goal_handle
