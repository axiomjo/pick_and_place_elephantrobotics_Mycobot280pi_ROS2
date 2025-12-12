
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup 
from mycobot280pi_interfaces.action import SimpleCommandsAction

ACTION_COMMAND_PRIMITIVES = '/planner/act_command_primitives'

class PrimitivesActionServer:
    """
    Manages the Action Server interface for long-running robot commands.
    It calls the core execution logic on the main node.
    """
    def __init__(self, node: Node, execute_command_callback):
        self.node = node
        # The method from the Orchestrator node to perform hardware moves
        self.execute_command_callback = execute_command_callback
        
        # Use a ReentrantCallbackGroup, as action execution (movement) can be long
        # and should not block other ROS callbacks like the service server.
        self.command_callback_group = ReentrantCallbackGroup()

        # Action Server Setup (for Planner)
        self._action_server = ActionServer(
            node=self.node,
            action_type=SimpleCommandsAction,
            action_name=ACTION_COMMAND_PRIMITIVES,
            execute_callback=self.execute_primitive_command_callback,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=self.command_callback_group
        )
        self.node.get_logger().info(f"Primitive Command Action Server '{ACTION_COMMAND_PRIMITIVES}' ready.")

    # --- ACTION CALLBACKS ---
    def _goal_callback(self, goal_request):
        """Called when a client sends a new goal."""
        self.node.get_logger().info(f'Received new action goal request: {goal_request.command_type}. Accepting.')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle):
        """Called when a client requests to cancel an active goal."""
        self.node.get_logger().info('Received cancel request. Allowing.')
        # NOTE: If implementing a stop command, it would be triggered here.
        return CancelResponse.ACCEPT
    
    def execute_primitive_command_callback(self, goal_handle):
        """Action execution runs in a worker thread provided by the MultiThreadedExecutor."""
        
        # Check for preemption/cancellation first
        if goal_handle.is_cancel_requested:
            goal_handle.canceled()
            self.node.get_logger().info(f"Action CANCELLED: {command_request.command_type}")
            
            result_msg = SimpleCommandsAction.Result()
            result_msg.success = False
            result_msg.message = "Execution cancelled."
            return result_msg
            
        command_request = goal_handle.request
        
        

        # Call the core execution logic on the main Orchestrator node
        self.node.get_logger().info(f"Action is EXECUTING: {command_request.command_type}")
        success, message = self.execute_command_callback(
            command_type=command_request.command_type,
            coords=command_request.coords,
            joint_angles=command_request.joint_angles,
            speed=command_request.speed,
            r=command_request.r, g=command_request.g, b=command_request.b
        )

        
        

        # Finalize the result
        if success:
            goal_handle.succeed()
            self.node.get_logger().info(f"Action SUCCEEDED: {command_request.command_type}")
        else:
            goal_handle.abort()
            self.node.get_logger().error(f"Action FAILED: {command_request.command_type}. {message}")
            
        result_msg = SimpleCommandsAction.Result()    
        result_msg.success = success
        result_msg.message = message
        
        return result_msg
