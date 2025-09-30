# prn_planning_logic.py

from . import prn_constants as const
from .prn_robot_commander import RobotCommander

class PlannerLogic:
    def __init__(self, node, commander: RobotCommander):
        self.node = node
        self.commander = commander
        self.state = "idle"  # States: "idle", "processing"

    def pick_and_place_object(self, obj, obj_target, obj_orientation, feedback_callback, goal_handle=None):
        self.node.get_logger().info(f"Starting pick and place for object ID: {obj.id}")
        self.state = "processing"

        # Define poses based on the object/target using constants
        pick_clearance_pose = [obj.center_point.x, obj.center_point.y, const.PLANE_HEIGHT_CLEARANCE, const.RX_DOWN, const.RY_DOWN, 0.0]
        pick_grasp_pose = [obj.center_point.x, obj.center_point.y, const.PICK_HEIGHT_Z, const.RX_DOWN, const.RY_DOWN, 0.0]
        place_clearance_pose = [obj_target.x, obj_target.y, const.PLANE_HEIGHT_CLEARANCE, const.RX_DOWN, const.RY_DOWN, float(obj_orientation)]
        place_drop_pose = [obj_target.x, obj_target.y, const.PICK_HEIGHT_Z, const.RX_DOWN, const.RY_DOWN, float(obj_orientation)]

        try:
            # --- PICKING SEQUENCE ---
            feedback_callback(f"Moving to pick clearance for object {obj.id}"); self.commander.set_rgb(*const.COLOR_CLEARANCE)
            if not self.commander.move_to_pose(pick_clearance_pose, const.DEFAULT_SPEED, goal_handle): return False
            
            feedback_callback("Descending to grasp"); self.commander.set_rgb(*const.COLOR_APPROACH)
            if not self.commander.move_to_pose(pick_grasp_pose, const.DEFAULT_SPEED, goal_handle): return False

            feedback_callback("Activating vacuum"); self.commander.set_rgb(*const.COLOR_GRASP)
            if not self.commander.set_vacuum("strong", goal_handle): return False
            
            feedback_callback("Lifting object"); self.commander.set_rgb(*const.COLOR_APPROACH)
            if not self.commander.move_to_pose(pick_clearance_pose, const.DEFAULT_SPEED, goal_handle): return False

            # --- PLACING SEQUENCE ---
            feedback_callback("Moving to place clearance"); self.commander.set_rgb(*const.COLOR_CLEARANCE)
            if not self.commander.move_to_pose(place_clearance_pose, const.DEFAULT_SPEED, goal_handle): return False
            
            feedback_callback("Descending to drop"); self.commander.set_rgb(*const.COLOR_APPROACH)
            if not self.commander.move_to_pose(place_drop_pose, const.DEFAULT_SPEED, goal_handle): return False

            feedback_callback("Deactivating vacuum"); self.commander.set_rgb(*const.COLOR_RELEASE)
            if not self.commander.set_vacuum("off", goal_handle): return False
            
            feedback_callback("Retreating from placed object"); self.commander.set_rgb(*const.COLOR_APPROACH)
            if not self.commander.move_to_pose(place_clearance_pose, const.DEFAULT_SPEED, goal_handle): return False

            # --- FINISH ---
            feedback_callback("Returning to home"); self.commander.set_rgb(*const.COLOR_HOME)
            if not self.commander.move_to_pose(const.HOME_POSE, const.DEFAULT_SPEED, goal_handle): return False

            self.node.get_logger().info(f"Finished processing object {obj.id}")
            # NOTE: State is reset in the action server's 'finally' block
            return True

        except Exception as e:
            self.node.get_logger().error(f"An exception occurred during PnP logic: {e}")
            self.commander.set_rgb(*const.COLOR_ERROR)
            # NOTE: State is reset in the action server's 'finally' block
            return False
