from rclpy.action import ActionServer, CancelResponse, GoalResponse
from mycobot280pi_interfaces.action import ProcessWorkspace

# --- Constants used by this module ---
ACTION_COMPLEX_COMMAND = '/gui/act_complex_command'

class ComplexCommandActionServer:
    def __init__(self, node, logic, callback_group):
        self.node = node
        self.logic = logic
        
        self._action_server = ActionServer(
            node=self.node,
            action_type=ProcessWorkspace,
            action_name=ACTION_COMPLEX_COMMAND,
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=callback_group
        )
        self.node.get_logger().info("Complex Command Action Server is ready.")

    def goal_callback(self, goal_request):
        self.node.get_logger().info('PLANNER Received new goal request from GUI. Accepting.') 
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.node.get_logger().info('PLANNER Received cancel request from GUI. Allowing.')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        self.node.get_logger().info("Executing goal...")

        objects = goal_handle.request.objects_to_move.objects
        target_positions = goal_handle.request.objects_target_position.points
        target_orientations = goal_handle.request.objects_target_orientation
        feedback_msg = ProcessWorkspace.Feedback()
        result_msg = ProcessWorkspace.Result()

        def publish_feedback(feedback_message):
            feedback_msg.current_state = feedback_message
            goal_handle.publish_feedback(feedback_msg)
            self.node.get_logger().info(f"Feedback: {feedback_message}")

        for idx, obj in enumerate(objects):
            if goal_handle.is_cancel_requested:
                result_msg.success = False
                result_msg.message = "Action canceled by user before starting new object."
                goal_handle.canceled()
                return result_msg

            self.node.get_logger().info(f"Processing object {idx+1}/{len(objects)} (ID: {obj.id}).")

            success, message = self.logic.pick_and_place_object(
                obj, target_positions[idx], target_orientations[idx],
                publish_feedback, goal_handle
            )
            
            if not success:
                if "CANCELLED" in message or "canceled by user" in message:
                    result_msg.success = False
                    result_msg.message = "Action canceled by user during execution."
                    goal_handle.canceled() 
                else:
                    result_msg.success = False
                    # CORRECTED: Use the actual failure message from the logic module.
                    result_msg.message = f"Pick and place failed for object {obj.id}. Detail: {message}"
                    goal_handle.abort()
                return result_msg

        result_msg.success = True
        result_msg.message = "All pick-and-place sequences completed successfully." 
        goal_handle.succeed()
        self.node.get_logger().info("Goal succeeded.")
        return result_msg
