# prn_action_client_server.py
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
import threading
import math  

from mycobot280pi_interfaces.action import ProcessWorkspace, SimpleCommandsAction

# Import the synchronous client wrapper we just made
from .prn_action_client_command_primitives import CommandPrimitivesActionClient

ACTION_COMPLEX_COMMAND = '/gui/act_complex_command'
RX_DOWN = 180.0
RY_DOWN = 0.0
DEFAULT_SPEED = 100

class PlannerNode(Node):
    def __init__(self):
        super().__init__('planner_node')
        self.get_logger().info("PlannerNode (SYNC) started.")
        
        # A lock to protect shared state (self.is_busy)
        self.logic_lock = threading.Lock()
        self.is_busy = False
        
        # This handle is not used for cancellation, but the logic
        # saves it, so we keep the variable.
        self.current_primitive_goal_handle = None 

        # A ReentrantCallbackGroup is CRITICAL. It allows a callback
        # (like execute_callback) to call the action client, which
        # in turn spins the node.
        self.callback_group = ReentrantCallbackGroup()

        # 1. Action Client (using our new sync wrapper)
        self.simple_cmd_client = CommandPrimitivesActionClient(
            self,
            callback_group=self.callback_group
        )
        
        # 2. Action Server
        self.process_ws_server = ActionServer(
            self,
            action_type=ProcessWorkspace,
            action_name=ACTION_COMPLEX_COMMAND,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            execute_callback=self.execute_callback,
            callback_group=self.callback_group
        )
        self.get_logger().info("ProcessWorkspace server is ready.")

    def goal_callback(self, goal_request):
        """Checks if the node is busy."""
        with self.logic_lock:
            if self.is_busy:
                self.get_logger().warn("HSM is busy, new goal REJECTED.")
                return GoalResponse.REJECT
            
            self.is_busy = True
            self.get_logger().info("New complex goal ACCEPTED.")
            return GoalResponse.ACCEPT
        
    def cancel_callback(self, cancel_request):
        """Accepts a cancel request."""
        # In a sync model, we can't interrupt the blocking
        # _execute_primitive_step.
        # We just accept the cancel, and the execute_callback loop
        # will see the 'is_cancel_requested' flag on its next iteration.
        self.get_logger().warn("Received CANCEL request from GUI. Will cancel between steps.")
        return CancelResponse.ACCEPT


#====================================== mbenerin planner=======

#====================================== mbenerin planner=======

    CONFIG = {
        "z_safe": 70.0,   
        "z_pick": 35.0,    
        "z_place": 42.0,   
        "step_size": 4.0, 
        "min_s_points": 5, 
        "speed_fast": 60, 
        "speed_slow": 30,  
        "colors": {
            "yellow": (255, 255, 0),    
            "red":    (255, 0, 0),      
            "purple": (128, 0, 128),    
            "green":  (0, 255, 0),      
            "blue":   (0, 0, 255),      
        }
    }

    PICK_AND_PLACE_STEPS = [
        {"phase": "Init",      "action": "rgb",   "color": "blue",   "desc": "System Ready"},
        {"phase": "Init",      "action": "joint", "target": "home",  "desc": "Home"},
        
        # PHASE 1: APPROACH
        {"phase": "Approach",  "action": "rgb",   "color": "yellow", "desc": "Approach"},
        {"phase": "Approach",  "action": "move",  "target": "pick_hover", "desc": "Hover Pick"},
        
        # PHASE 2: PICK
        {"phase": "Pick",      "action": "rgb",   "color": "red",    "desc": "Pick Mode"},
        {"phase": "Pick",      "action": "tool",  "state": "on",     "desc": "Vacuum ON"},
        {"phase": "Pick",      "action": "s_curve", "target": "pick_down", "desc": "Descend"},
        {"phase": "Pick",      "action": "s_curve", "target": "pick_hover", "desc": "Lift"},

        # PHASE 3: TRANSPORT (Linear Path = No dipping)
        {"phase": "Transport", "action": "rgb",   "color": "purple", "desc": "Transport Mode"},
        {"phase": "Transport", "action": "linear_path",  "target": "place_hover", "desc": "Safe Transport"},

        # PHASE 4: PLACE
        {"phase": "Place",     "action": "rgb",   "color": "green",  "desc": "Place Mode"},
        {"phase": "Place",     "action": "s_curve", "target": "place_down", "desc": "Descend"},
        {"phase": "Place",     "action": "tool",  "state": "off",    "desc": "Vacuum OFF"},
        {"phase": "Place",     "action": "s_curve", "target": "place_hover", "desc": "Retract"},
        
        # FINISH
        {"phase": "Finish",    "action": "rgb",   "color": "blue",   "desc": "Complete"},
        {"phase": "Finish",    "action": "joint", "target": "home",  "desc": "Home"},
    ]

    def _generate_s_points(self, start_z, end_z):
        dist = abs(end_z - start_z)
        steps = max(int(math.ceil(dist / self.CONFIG["step_size"])), self.CONFIG["min_s_points"])
        points = []
        for i in range(1, steps + 1):
            t = i / steps
            t_smooth = (1 - math.cos(t * math.pi)) / 2
            val = start_z + (end_z - start_z) * t_smooth
            points.append(val)
        return points

    def _generate_3d_path(self, start_pose, end_pose):
        dx, dy, dz = end_pose[0]-start_pose[0], end_pose[1]-start_pose[1], end_pose[2]-start_pose[2]
        dist = math.sqrt(dx**2 + dy**2 + dz**2)
        steps = max(int(math.ceil(dist / self.CONFIG["step_size"])), self.CONFIG["min_s_points"])
        
        points = []
        for i in range(1, steps + 1):
            t = i / steps
            points.append([
                start_pose[0] + dx * t,
                start_pose[1] + dy * t,
                start_pose[2] + dz * t, # Linear Z (straight line)
                end_pose[3], end_pose[4], end_pose[5]
            ])
        return points

    def _resolve_target(self, target_name, obj, tgt, orientation):
        c = self.CONFIG
        if "pick" in target_name:
            x, y, rz = float(obj.center_point.x), float(obj.center_point.y), 0.0
        elif "place" in target_name:
            x, y = float(tgt.x), float(tgt.y)
            rz = float(orientation) if orientation else 0.0
        elif "home" in target_name:
            return None
        else:
            return None # Should not happen

        if "hover" in target_name: z = c["z_safe"]
        elif "pick_down" in target_name: z = c["z_pick"]
        elif "place_down" in target_name: z = c["z_place"]
        else: z = c["z_safe"]

        return [x, y, float(z), RX_DOWN, RY_DOWN, float(rz)]

    def _generate_all_steps(self, objects, targets, orientations):
        ALL_STEPS = []
        current_z = float(self.CONFIG["z_safe"])

        for obj_idx, (obj, tgt, orient) in enumerate(zip(objects, targets, orientations)):
            for step in self.PICK_AND_PLACE_STEPS:
                action = step["action"]
                desc = step.get("desc", "")

                if action == "s_curve":
                    target_pose = self._resolve_target(step["target"], obj, tgt, orient)
                    z_points = self._generate_s_points(current_z, target_pose[2])
                    for z in z_points:
                        goal = SimpleCommandsAction.Goal()
                        goal.command_type = 'move'
                        goal.speed = int(self.CONFIG["speed_slow"])
                        goal.coords = list(target_pose)
                        goal.coords[2] = float(z)
                        ALL_STEPS.append((goal, desc, obj))
                    current_z = target_pose[2]

                elif action == "linear_path":
                    target_pose = self._resolve_target(step["target"], obj, tgt, orient)
                    
                    # Safe start pose retrieval
                    start_pose = [obj.center_point.x, obj.center_point.y, current_z, RX_DOWN, RY_DOWN, 0.0]
                    if ALL_STEPS and hasattr(ALL_STEPS[-1][0], 'coords') and len(ALL_STEPS[-1][0].coords) == 6:
                        start_pose = ALL_STEPS[-1][0].coords

                    path_points = self._generate_3d_path(start_pose, target_pose)
                    for pt in path_points:
                        goal = SimpleCommandsAction.Goal()
                        goal.command_type = 'move'
                        goal.speed = int(self.CONFIG["speed_fast"])
                        goal.coords = pt
                        ALL_STEPS.append((goal, desc, obj))
                    current_z = target_pose[2]

                elif action == "move":
                    target_pose = self._resolve_target(step["target"], obj, tgt, orient)
                    goal = SimpleCommandsAction.Goal()
                    goal.command_type = 'move'
                    goal.speed = int(self.CONFIG["speed_fast"])
                    goal.coords = list(target_pose)
                    ALL_STEPS.append((goal, desc, obj))
                    current_z = target_pose[2]

                elif action == "tool":
                    goal = SimpleCommandsAction.Goal()
                    goal.command_type = 'vacuum_strong' if step.get("state") == "on" else 'vacuum_off'
                    ALL_STEPS.append((goal, desc, obj))

                elif action == "rgb":
                    goal = SimpleCommandsAction.Goal()
                    goal.command_type = 'set_rgb'
                    rgb = self.CONFIG["colors"].get(step.get("color"), (0,0,0))
                    goal.r, goal.g, goal.b = [int(x) for x in rgb]
                    ALL_STEPS.append((goal, desc, obj))

                elif action == "joint":
                    goal = SimpleCommandsAction.Goal()
                    goal.command_type = 'move_joints'
                    goal.speed = int(self.CONFIG["speed_fast"])
                    goal.joint_angles = [0.0]*6
                    ALL_STEPS.append((goal, desc, obj))

        return ALL_STEPS
        
    def execute_callback(self, goal_handle):
        self.get_logger().info("Starting new complex plan...")
        request = goal_handle.request
        result = ProcessWorkspace.Result()
        
        # 1. Generate Plan
        try:
            steps = self._generate_all_steps(
                request.objects_to_move.objects, 
                request.objects_target_position.points, 
                request.objects_target_orientation
            )
        except Exception as e:
            self.get_logger().error(f"Plan generation failed: {e}")
            goal_handle.abort()
            result.success = False
            result.message = str(e)
            return result

        # 2. Execute Steps Loop
        total = len(steps)
        for i, (cmd, desc, obj) in enumerate(steps):
            # Check for cancellation
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result.success = False
                result.message = "Cancelled by user"
                return result

            # Feedback
            feedback = ProcessWorkspace.Feedback()
            feedback.current_state = f"[{i+1}/{total}] {desc}"
            feedback.current_object = obj
            goal_handle.publish_feedback(feedback)

            # Send to Primitive Client (Blocking)
            success, msg, _ = self.simple_cmd_client.send_goal(cmd)

            if not success:
                goal_handle.abort()
                result.success = False
                result.message = f"Failed at {desc}: {msg}"
                return result

        # 3. Finish
        goal_handle.succeed()
        result.success = True
        result.message = "Complete"
        return result
#====================================== mbenerin planner=======

#====================================== mbenerin planner=======


    def _execute_primitive_step(self, cmd_goal: SimpleCommandsAction.Goal, description: str, feedback_callback, complex_goal_handle):
        """
        Helper method copied from PlannerLogicActionClient.
        Calls the synchronous action client.
        """
        feedback_callback(f"Executing step: {description}")

        # This check is redundant if the main loop checks, but good for safety.
        if complex_goal_handle.is_cancel_requested:
            return False, "CANCELLED"

        # This is the BLOCKING call.
        success, message, new_goal_handle = self.simple_cmd_client.send_goal(cmd_goal)
        
        with self.logic_lock:
            self.current_primitive_goal_handle = new_goal_handle

        if not success:
            self.get_logger().error(f"Primitive command FAILED: {description}. Message: {message}")
            feedback_callback(f"ERROR: {description} failed. {message}")
            return False, message
        else:
            self.get_logger().info(f"Primitive command SUCCEEDED: {description}")
            return True, message
