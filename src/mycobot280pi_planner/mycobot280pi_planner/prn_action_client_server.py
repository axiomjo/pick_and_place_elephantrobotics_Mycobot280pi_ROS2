# prn_action_client_server.py
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
import threading
import time  # <--- IMPORT ADDED

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

PICK_AND_PLACE_STEPS = [
        # 1. RGB: Blue (Start)
        ("set_rgb", "Set RGB Blue (Start)", 0, None, "BLUE", {"r": 0, "g": 0, "b": 255}),

        # 2. Home Position
        ("move_joints", "Go to Home", 100, None, "home", {"joints": [0, 0, 0, 0, 0, 0]}),

        # 3. Approach Object (Safe Height)
        ("move", "Approach Object (Hover)", 100, 150.0, "pick", None),

        # 4. Descend to Object (Pick Height)
        ("move", "Descend to Object", 50, 60.0, "pick", None),

        # 5. RGB: Red (Picking)
        ("set_rgb", "Set RGB Red (Picking)", 0, None, "fixed", {"r": 255, "g": 0, "b": 0}),

        # 6. Vacuum On
        ("vacuum_strong", "Vacuum ON", 0, None, "fixed", None),

        # 7. Lift Object (Safe Height)
        ("move", "Lift Object", 80, 150.0, "pick", None),

        # 8. Move to Target (Hover)
        ("move", "Move to Target (Hover)", 100, 150.0, "place", None),

        # 9. Descend to Target (Place Height)
        ("move", "Descend to Target", 50, 60.0, "place", None),

        # 10. RGB: Green (Placing)
        ("set_rgb", "Set RGB Green (Placing)", 0, None, "fixed", {"r": 0, "g": 255, "b": 0}),

        # 11. Vacuum Off
        ("vacuum_off", "Vacuum OFF", 0, None, "fixed", None),

        # 12. Lift After Place
        ("move", "Retract after place", 80, 150.0, "place", None),
        
        # 13. RGB: Blue (Done)
        ("set_rgb", "Set RGB Blue (Done)", 0, None, "fixed", {"r": 0, "g": 0, "b": 255}),
    ]





    def _generate_all_steps(self, objects, targets, orientations)):
        """
        Factory method that generates the full list of goal steps for all objects.
        Returns a list of tuples: (SimpleCommandsAction.Goal, description_string, OneDetectedObject_msg)
        """
        
        ALL_STEPS = []
        
        for i, (obj, tgt, orient) in enumerate(zip(objects, targets, orientations)):
        
            for step in PICK_AND_PLACE_STEPS:
            
                cmd_type, desc, speed, z_h, intent, params = step
                
                goal = SimpleCommandsAction.Goal()
                goal.command_type = cmd_type
                
                if cmd_type == 'move':
                    goal.speed = speed
                    
                    # Determine X, Y, and Rotation based on source
                    if source == 'pick':
                        target_x = obj.center_point.x
                        target_y = obj.center_point.y
                        target_rz = 0.0 # Picking usually aligns with base or 0
                    elif source == 'place':
                        target_x = tgt.x
                        target_y = tgt.y
                        target_rz = float(orient) # Use user-specified orientation for placing
                    else:
                        # Fallback for fixed coords if needed
                        target_x, target_y, target_rz = 0.0, 0.0, 0.0

                    # Construct the 6D coordinate list [x, y, z, rx, ry, rz]
                    goal.coords = [
                        target_x, 
                        target_y, 
                        float(z_h), 
                        RX_DOWN, 
                        RY_DOWN, 
                        target_rz
                    ]

                # Handle Joint Moves
                elif cmd_type == 'move_joints':
                    goal.speed = speed
                    if params and 'joints' in params:
                        goal.joint_angles = [float(x) for x in params['joints']]

                # Handle RGB
                elif cmd_type == 'set_rgb':
                    if params:
                        goal.r = params.get('r', 0)
                        goal.g = params.get('g', 0)
                        goal.b = params.get('b', 0)

                # Handle Vacuum (No extra params needed usually)
                elif 'vacuum' in cmd_type:
                    pass

                # Append the fully constructed step to the master sequence
                # We store 'obj' so feedback knows which object is currently being manipulated
                ALL_STEPS.append((goal, desc, obj))

        return ALL_STEPS
            
        
    def execute_callback(self, goal_handle):
        """
        Decoupled execution callback. 
        1. Generates steps.
        2. Executes steps linearly.
        3. Handles Feedback & Cancellation.
        """
        self.get_logger().info("Starting ProcessWorkspace execution...")
        result = ProcessWorkspace.Result()

        # 1. DATA EXTRACTION
        try:
            objects_to_move = goal_handle.request.objects_to_move.objects
            target_positions = goal_handle.request.objects_target_position.points
            target_orientations = goal_handle.request.objects_target_orientation

            if not (len(objects_to_move) == len(target_positions) == len(target_orientations)):
                raise ValueError("Mismatched goal lists input.")

            # 2. GENERATION
            # Generate the entire stack of moves for ALL objects at once
            all_steps = self._generate_all_steps(
                objects_to_move, target_positions, target_orientations
            )
            
            self.get_logger().info(f"Generated {len(all_steps)} steps for {len(objects_to_move)} objects.")

        except Exception as e:
            self.get_logger().error(f"Generation Failed: {e}")
            result.success = False
            result.message = f"Input Data Error: {e}"
            goal_handle.abort()
            return result

        # Define local feedback helper
        def publish_feedback(state_msg, object_msg):
            feedback = ProcessWorkspace.Feedback()
            feedback.current_state = state_msg
            feedback.current_object = object_msg
            goal_handle.publish_feedback(feedback)

        # 3. EXECUTION LOOP
        all_succeeded = True

        for i, (goal, description, current_obj) in enumerate(all_steps):
            
            # A. Check for Cancellation
            if goal_handle.is_cancel_requested:
                self.get_logger().warn("Goal Canceled by Client.")
                publish_feedback("CANCELED", current_obj)
                goal_handle.canceled()
                result.success = False
                result.message = "Canceled by user."
                return result

            # B. Publish Pre-Execution Feedback
            publish_feedback(f"Step {i+1}/{len(all_steps)}: {description}", current_obj)

            # C. Execute Primitive Step (Blocking Call)
            # Note: We pass a simple lambda for the inner feedback if needed, 
            # or just rely on the outer feedback we just sent.
            success, msg = self._execute_primitive_step(
                goal, 
                description, 
                lambda x: None, # Inner feedback silencer, or pass a real logger
                goal_handle
            )

            if not success:
                self.get_logger().error(f"Step Failed: {description} -> {msg}")
                publish_feedback(f"FAILED: {description}", current_obj)
                all_succeeded = False
                result.message = f"Failure at step '{description}': {msg}"
                break
            
            # Optional: Sleep for stability if it's a move command
            if "move" in goal.command_type:
                time.sleep(0.5)

        # 4. FINALIZATION
        if all_succeeded:
            result.success = True
            result.message = "All objects processed successfully."
            goal_handle.succeed()
        else:
            result.success = False
            # Message already set in loop
            goal_handle.abort()

        # Reset flags (Safety)
        with self.logic_lock:
            self.is_busy = False
            self.current_primitive_goal_handle = None

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
