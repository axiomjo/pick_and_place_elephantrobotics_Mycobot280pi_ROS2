# prn_action_server.py

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from mycobot280pi_interfaces.action import ProcessWorkspace

ACTION_COMPLEX_COMMAND = '/planner/act_complex_command'


class PlannerActionServer:
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
        
        self.node.get_logger().info("Action server for complex commands is ready.")

    def goal_callback(self, goal_request):
        """Always accept new goals (planner is now stateless)."""
        self.node.get_logger().info('Received new goal request. Accepting.')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        """Always allow cancellation."""
        self.node.get_logger().info('Received cancel request.')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        """Runs pick-and-place sequence for each object (fire-and-forget)."""
        self.node.get_logger().info("Executing goal...")

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

            # Just fire off the commands, no waiting
            self.logic.pick_and_place_object(
                obj, target_positions[idx], target_orientations[idx],
                publish_feedback, goal_handle
            )

        result_msg.success = True
        result_msg.message = "All pick-and-place commands sent."
        goal_handle.succeed()
        self.node.get_logger().info("Goal succeeded.")
        return result_msg

