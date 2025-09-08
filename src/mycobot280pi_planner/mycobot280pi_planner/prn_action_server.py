"""
prn_action_server.py

Implements the /planner/process_workspace action server for the planner node.
Receives a list of objects to move (with their target positions/orientations) from the GUI,
and coordinates the pick-and-place sequence for each object, providing feedback as it works.
"""

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from mycobot280pi_interfaces.action import ProcessWorkspace
from mycobot280pi_interfaces.msg import OneDetectedObject, ManyDetectedObjects, Point2DArray

class PlannerActionServer:
    def __init__(self, node, logic):
        self.node = node
        self.logic = logic
        self._action_server = ActionServer(
            node,
            ProcessWorkspace,
            '/planner/process_workspace',
            self.execute_callback
        )

    async def execute_callback(self, goal_handle):
        self.node.get_logger().info("Received process_workspace action goal.")

        objects = goal_handle.request.objects_to_move.objects
        target_positions = goal_handle.request.objects_target_position.points
        target_orientation = goal_handle.request.objects_target_orientation

        feedback_msg = ProcessWorkspace.Feedback()
        result_msg = ProcessWorkspace.Result()

        try:
            # Check that the number of objects matches the number of target positions
            if len(objects) != len(target_positions):
                result_msg.success = False
                result_msg.message = "Mismatch between objects and target positions."
                goal_handle.abort()
                return result_msg

            for idx, obj in enumerate(objects):
                # Assign target position and orientation to the object (if needed)
                obj_target = target_positions[idx]
                # Optionally, you can add orientation to obj if your message supports it

                # Call planning logic to process this object
                # This should break down the task and publish atomic commands
                async for state in self.logic.pick_and_place_object(obj, obj_target, target_orientation):
                    feedback_msg.current_state = state
                    feedback_msg.current_object = obj
                    goal_handle.publish_feedback(feedback_msg)
                    await rclpy.sleep(0.1)  # Simulate work or wait for real feedback

            result_msg.success = True
            result_msg.message = "All objects processed successfully."
            goal_handle.succeed()
        except Exception as e:
            result_msg.success = False
            result_msg.message = f"Error: {e}"
            goal_handle.abort()
        return result_msg
