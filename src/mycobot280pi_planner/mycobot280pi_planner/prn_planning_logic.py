from mycobot280pi_interfaces.action import SimpleCommandsAction
from .prn_action_client_command_primitives import CommandPrimitivesActionClient

# --- Constants used by this module ---
RX_DOWN = 180.0
RY_DOWN = 0.0
DEFAULT_SPEED = 100


class PlannerLogicActionClient:
    def __init__(self, node, callback_group):
        self.node = node
        self.action_client = CommandPrimitivesActionClient(self.node, callback_group)
        self.current_primitive_goal_handle = None 

    def _execute_primitive_step(self, cmd_goal: SimpleCommandsAction.Goal, description: str, feedback_callback, complex_goal_handle):
        """
        Receives a SimpleCommandsAction.Goal object, passes it to the Action Client,
        and returns the success status and message from the Executor.
        """
        feedback_callback(f"Executing step: {description}")

        if complex_goal_handle.is_cancel_requested:
            return False, "CANCELLED"

        success, message, new_goal_handle = self.action_client.send_goal(cmd_goal)
        self.current_primitive_goal_handle = new_goal_handle

        if not success:
            self.node.get_logger().error(f"Primitive command FAILED: {description}. Message: {message}")
            feedback_callback(f"ERROR: {description} failed. {message}")
            return False, message
        else:
            self.node.get_logger().info(f"Primitive command SUCCEEDED: {description}")
            return True, message

        

    def pick_and_place_object(self, obj, obj_target, obj_orientation, feedback_callback, goal_handle):
        feedback_callback(f"Starting pick and place for object {obj.id}")

        steps = [
            # 0. RGB: BLUE (Preparing / Home)
            (SimpleCommandsAction.Goal(
                command_type="set_rgb",
                r=0, g=0, b=255
            ), "set RGB to blue (ready/home)"),

            # 1. GO HOME (Initial State)
            (SimpleCommandsAction.Goal(
                command_type="move_joints",
                joint_angles=[0, 0, 0, 0, 0, 0],
                speed=100
            ), "return to home position (angles 0)"),

            # 2. RGB: YELLOW (Approaching object)
            (SimpleCommandsAction.Goal(
                command_type="set_rgb",
                r=255, g=255, b=0
            ), "set RGB to yellow (approaching object)"),

            # 3. GOTO ABOVE OBJECT (Z=70)
            (SimpleCommandsAction.Goal(
                command_type="move_blockingmode",
                coords=[obj.center_point.x, obj.center_point.y, 70.0, RX_DOWN, RY_DOWN, 0.0],
                speed=100
            ), "move above object (Z=70, RZ=0)"),

            # 4. RGB: RED (Picking)
            (SimpleCommandsAction.Goal(
                command_type="set_rgb",
                r=255, g=0, b=0
            ), "set RGB to red (picking object)"),

            # 5. ACTIVATE VACUUM STRONG
            (SimpleCommandsAction.Goal(
                command_type="vacuum_strong",
            ), "activate vacuum strong"),

            # 6. DESCEND TO OBJECT HEIGHT (Z=30)
            (SimpleCommandsAction.Goal(
                command_type="move_blockingmode",
                coords=[obj.center_point.x, obj.center_point.y, 30.0, RX_DOWN, RY_DOWN, 0.0],
                speed=50
            ), "descend exactly to object (Z=30)"),

            # 7. LIFT UP to safe place
            (SimpleCommandsAction.Goal(
                command_type="move_joints",
                joint_angles=[0, 0, 0, 0, 0, 0],
                speed=100
            ), "return to home position (angles 0)"),

            # 8. RGB: GREEN (Placing)
            (SimpleCommandsAction.Goal(
                command_type="set_rgb",
                r=0, g=255, b=0
            ), "set RGB to green (placing object)"),

            # 9. MOVE TO ABOVE PLACE POSITION (Z=70)
            (SimpleCommandsAction.Goal(
                command_type="move_blockingmode",
                coords=[obj_target.x, obj_target.y, 70.0, RX_DOWN, RY_DOWN, float(obj_orientation)],
                speed=100
            ), "move to above place position (Z=70, RZ=User)"),

            # 10. DESCEND TO PLACE POSITION (Z=30)
            (SimpleCommandsAction.Goal(
                command_type="move_blockingmode",
                coords=[obj_target.x, obj_target.y, 30.0, RX_DOWN, RY_DOWN, float(obj_orientation)],
                speed=50
            ), "descend to final placement height (Z=30)"),

            # 11. DEACTIVATE VACUUM
            (SimpleCommandsAction.Goal(
                command_type="vacuum_off",
            ), "deactivate vacuum"),

            # 12. LIFT UP (Z=70)
            (SimpleCommandsAction.Goal(
                command_type="move_blockingmode",
                coords=[obj_target.x, obj_target.y, 70.0, RX_DOWN, RY_DOWN, float(obj_orientation)],
                speed=DEFAULT_SPEED
            ), "lift up after place (Z=70)"),

            # 13. RGB: BLUE (Return to idle)
            (SimpleCommandsAction.Goal(
                command_type="set_rgb",
                r=0, g=0, b=255
            ), "set RGB to blue (done/idle)")
        ]

        for cmd, description in steps:
            if goal_handle.is_cancel_requested:
                feedback_callback("Sequence CANCELLED.")
                return False, "Action canceled by user."
            
            success, message = self._execute_primitive_step(
                cmd, description, feedback_callback, goal_handle
            )
            
            if not success:
                return False, message

        feedback_callback(f"Finished pick and place for object {obj.id}")
        return True, "Pick and place sequence completed."
