import rclpy
from rclpy.action import ActionClient
from mycobot280pi_interfaces.action import SimpleCommandsAction

# --- Constants used by this module ---
ACTION_COMMAND_PRIMITIVES = '/planner/act_command_primitives' 
WAIT_TIMEOUT_SEC = 5.0

class CommandPrimitivesActionClient:
    def __init__(self, node, callback_group):
        self.node = node
        self._action_client = ActionClient(
            node, 
            SimpleCommandsAction,
            ACTION_COMMAND_PRIMITIVES,
            callback_group=callback_group
        )
        self.current_goal_handle = None 
        self.node.get_logger().info(" PLANNER Action Client for Command Primitives is ready.")

    def send_goal(self, primitive_cmd_goal: SimpleCommandsAction.Goal):
        """
        Sends a primitive action goal and waits for the result (blocking).
        :param primitive_cmd_goal: A SimpleCommandsAction.Goal object.
        :return: Tuple (success: bool, message: str, goal_handle)
        """
        self.node.get_logger().info(f"Waiting for EXECUTOR's command primitives action server: {ACTION_COMMAND_PRIMITIVES}...")
        if not self._action_client.wait_for_server(timeout_sec=WAIT_TIMEOUT_SEC):
            self.node.get_logger().error("PLANNER Command Primitives Action Server is not available!")
            return False, "Primitive Action Server not available.", None

        self.node.get_logger().info(f"Sending primitive goal: {primitive_cmd_goal.command_type}")
        
        send_goal_future = self._action_client.send_goal_async(primitive_cmd_goal)
        rclpy.spin_until_future_complete(self.node, send_goal_future)
        goal_handle = send_goal_future.result()
        
        if not goal_handle.accepted:
            self.node.get_logger().error("Primitive goal rejected by EXECUTOR action server.")
            return False, "Primitive goal rejected by EXECUTOR action server.", None
        
        self.current_goal_handle = goal_handle    
        self.node.get_logger().info('Primitive goal accepted. Waiting for result...')

        get_result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self.node, get_result_future)
        
        result_response = get_result_future.result()
        result_data = result_response.result
        
        self.current_goal_handle = None
        
        return result_data.success, result_data.message, goal_handle

    def cancel_current_goal(self):
        """
        Sends a cancellation signal to the currently active primitive action goal.
        """
        if self.current_goal_handle is None:
            self.node.get_logger().info("No active primitive goal to cancel in Planner.")
            return True

        self.node.get_logger().warn(f"Sending Cancellation Request for Goal ID: {self.current_goal_handle.goal_id}")
        
        cancel_future = self._action_client.cancel_goal_async(self.current_goal_handle)
        rclpy.spin_until_future_complete(self.node, cancel_future)
        
        if cancel_future.result():
            self.node.get_logger().warn("Cancellation Request accepted by Executor.")
            return True
        else:
            self.node.get_logger().error("Failed to send Cancellation Request.")
            return False
