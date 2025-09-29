# prn_action_server.py

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from mycobot280pi_interfaces.action import ProcessWorkspace

class PlannerActionServer:
    def __init__(self, node, logic, callback_group):
        self.node = node
        self.logic = logic
        self._action_server = ActionServer(
            node,
            ProcessWorkspace,
            '/planner/act_complex_command',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=callback_group
        )
        self.node.get_logger().info("Action server for complex commands is ready.")

    def goal_callback(self, goal_request):
        """Accepts or rejects a new goal."""
        self.node.get_logger().info('Received new goal request...')
        if self.logic.state != "idle":
            self.node.get_logger().warn('Planner is busy! Rejecting new goal.')
            return GoalResponse.REJECT
        self.node.get_logger().info('Planner is idle. Accepting new goal.')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        """Accepts or rejects a client request to cancel an action."""
        self.node.get_logger().info('Received cancel request.')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        """This function runs the entire pick-and-place process."""
        self.node.get_logger().info("Executing goal...")

        try:
            objects = goal_handle.request.objects_to_move.objects
            target_positions = goal_handle.request.objects_target_position.points
            target_orientations = goal_handle.request.objects_target_orientation

            feedback_msg = ProcessWorkspace.Feedback()
            result_msg = ProcessWorkspace.Result()

            def publish_feedback(state_from_logic):
                feedback_msg.current_state = state_from_logic
                goal_handle.publish_feedback(feedback_msg)
                self.node.get_logger().info(f"Feedback: {state_from_logic}")

            for idx, obj in enumerate(objects):
                if goal_handle.is_cancel_requested:
                    result_msg.success = False
                    result_msg.message = "Action canceled by user."
                    goal_handle.canceled()
                    return result_msg

                self.node.get_logger().info(f"Processing object {idx+1}/{len(objects)} (ID: {obj.id}).")
                
                was_successful = self.logic.pick_and_place_object(
                    obj, target_positions[idx], target_orientations[idx], 
                    publish_feedback, goal_handle
                )

                if not was_successful:
                    result_msg.success = False
                    result_msg.message = f"Action failed while processing object ID {obj.id}."
                    goal_handle.abort()
                    return result_msg

            result_msg.success = True
            result_msg.message = "All objects processed successfully."
            goal_handle.succeed()
            self.node.get_logger().info("Goal succeeded.")
            return result_msg

        finally:
            # This guarantees the planner state is reset, no matter what happens.
            self.node.get_logger().info("Action finished. Resetting planner state to 'idle'.")
            self.logic.state = "idle"
