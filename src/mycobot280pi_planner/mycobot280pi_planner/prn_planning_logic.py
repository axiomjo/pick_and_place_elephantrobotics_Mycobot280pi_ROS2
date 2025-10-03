# prn_planning_logic.py
import rclpy
from mycobot280pi_interfaces.msg import SimpleCommands
from .prn_constants import PLANE_HEIGHT_CLEARANCE, PICK_HEIGHT_Z, RX_DOWN, RY_DOWN, DEFAULT_SPEED, HOME_POSE


class PlannerLogic:
    def __init__(self, node, feedback_callback_group):
        self.node = node
        self.command_pub = None

    def set_command_publisher(self, pub):
        self.command_pub = pub

    def _publish_command(self, cmd: SimpleCommands, description: str = ""):
        """Fire-and-forget command publisher."""
        if self.command_pub:
            self.command_pub.publish(cmd)
            self.node.get_logger().info(f"[Planner] Published command: {cmd.command_type} {description}")
        else:
            self.node.get_logger().error("Command publisher not set!")

    def pick_and_place_object(self, obj, obj_target, obj_orientation, feedback_callback, goal_handle):
        """
        Fire-and-forget pick and place sequence.
        No blocking, no waiting for feedback.
        """

        feedback_callback(f"Starting pick and place for object {obj.id}")

        # --- Step 1: Move above pick position ---
        pick_pose = [obj.center_point.x, obj.center_point.y, PLANE_HEIGHT_CLEARANCE, RX_DOWN, RY_DOWN, 0.0]
        cmd = SimpleCommands(command_type="move", coords=pick_pose, speed=DEFAULT_SPEED)
        self._publish_command(cmd, "above pick position")

        # --- Step 2: Descend to pick height ---
        pick_pose_down = [obj.center_point.x, obj.center_point.y, PICK_HEIGHT_Z, RX_DOWN, RY_DOWN, 0.0]
        cmd = SimpleCommands(command_type="move", coords=pick_pose_down, speed=DEFAULT_SPEED)
        self._publish_command(cmd, "pick position")

        # --- Step 3: Activate vacuum ---
        cmd = SimpleCommands(command_type="vacuum_on")
        self._publish_command(cmd, "vacuum ON")

        # --- Step 4: Move above place position ---
        place_pose = [obj_target.x, obj_target.y, PLANE_HEIGHT_CLEARANCE, RX_DOWN, RY_DOWN, float(obj_orientation)]
        cmd = SimpleCommands(command_type="move", coords=place_pose, speed=DEFAULT_SPEED)
        self._publish_command(cmd, "above place position")

        # --- Step 5: Descend to place height ---
        place_pose_down = [obj_target.x, obj_target.y, PICK_HEIGHT_Z, RX_DOWN, RY_DOWN, float(obj_orientation)]
        cmd = SimpleCommands(command_type="move", coords=place_pose_down, speed=DEFAULT_SPEED)
        self._publish_command(cmd, "place position")

        # --- Step 6: Deactivate vacuum ---
        cmd = SimpleCommands(command_type="vacuum_off")
        self._publish_command(cmd, "vacuum OFF")

        # --- Step 7: Return to home ---
        cmd = SimpleCommands(command_type="move", coords=HOME_POSE, speed=DEFAULT_SPEED)
        self._publish_command(cmd, "home position")

        feedback_callback(f"Finished pick and place for object {obj.id}")
        return True  # Always returns true, executor decides actual success

    def manual_command_callback(self, msg):
        """Forward manual commands directly to executor."""
        self._publish_command(msg, "manual forward")

