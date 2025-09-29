# prn_action_server.py

import rclpy
from rclpy.action import ActionServer
from mycobot280pi_interfaces.action import ProcessWorkspace

class PlannerActionServer:
    def __init__(self, node, logic, callback_group):
        self.node = node
        self.logic = logic
        self._action_server = ActionServer(
            node,
            ProcessWorkspace,
            '/planner/act_complex_command',
            self.execute_callback,
            callback_group=callback_group
        )
        self.node.get_logger().info("Action server for complex commands is ready.")

    def execute_callback(self, goal_handle):
        self.node.get_logger().info("Received 'ProcessWorkspace' action goal.")

        objects = goal_handle.request.objects_to_move.objects
        target_positions = goal_handle.request.objects_target_position.points
        target_orientations = goal_handle.request.objects_target_orientation

        feedback_msg = ProcessWorkspace.Feedback()
        result_msg = ProcessWorkspace.Result()

        if len(objects) != len(target_positions):
            result_msg.success = False
            result_msg.message = "Mismatch between objects and target positions."
            goal_handle.abort()
            return result_msg

        # Definisikan fungsi helper untuk menerbitkan feedback
        def publish_feedback(state_from_logic):
            if not rclpy.ok() or goal_handle.is_cancel_requested:
                return
            
            # Variabel 'state_from_logic' hanya ada di dalam fungsi ini
            feedback_msg.current_state = state_from_logic
            goal_handle.publish_feedback(feedback_msg)
            self.node.get_logger().info(f"Feedback: {state_from_logic}")

        try:
            for idx, obj in enumerate(objects):
                self.node.get_logger().info(f"Processing object {idx+1}/{len(objects)} (ID: {obj.id}).")
                
                # Update 'current_object' di pesan feedback untuk objek ini
                feedback_msg.current_object = obj
                
                obj_target = target_positions[idx]

                # Ambil orientasi untuk objek saat ini
                target_orientation_for_obj = target_orientations[idx]

                # Teruskan orientasi ke fungsi logic
                was_successful = self.logic.pick_and_place_object(
        obj, obj_target, target_orientation_for_obj, publish_feedback, goal_handle
    )

                # Check if the logic was cancelled or failed
                if not was_successful:
                    # The is_cancel_requested check inside the logic already caught it.
                    # We just need to formalize it here.
                    if goal_handle.is_cancel_requested:
                        goal_handle.canceled()
                        result_msg.success = False
                        result_msg.message = "Action canceled during object processing."
                    else:
                        # Handle non-cancellation failures (e.g., robot couldn't reach)
                        goal_handle.abort()
                        result_msg.success = False
                        result_msg.message = f"Action failed while processing object ID {obj.id}."

                    return result_msg # Exit the callback


            result_msg.success = True
            result_msg.message = "All objects processed successfully."
            goal_handle.succeed()

        except Exception as e:
            # BAGIAN INI MEMASTIKAN MASALAH #2 TIDAK TERJADI
            # Jangan gunakan variabel 'state' di sini karena ia tidak ada di lingkup ini
            error_msg = f"An exception occurred: {e}"
            self.node.get_logger().error(error_msg)
            result_msg.success = False
            result_msg.message = error_msg
            goal_handle.abort()
        
        return result_msg
