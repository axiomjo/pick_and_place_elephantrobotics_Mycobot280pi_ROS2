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
        
    def execute_callback(self, goal_handle):
        """
        Executes the logic from PlannerLogicActionClient,
        in a blocking, synchronous way.
        """
        self.get_logger().info("Starting execution of complex goal...")
        
        # Create a feedback callback
        def feedback_callback(msg: str):
            feedback = ProcessWorkspace.Feedback()
            feedback.current_state = msg
            goal_handle.publish_feedback(feedback)
        
        result = ProcessWorkspace.Result()
        

        try:
            
            objects_to_move = goal_handle.request.objects_to_move.objects
            target_positions = goal_handle.request.objects_target_position.points
            target_orientations = goal_handle.request.objects_target_orientation
        
            if not (len(objects_to_move) == len(target_positions) == len(target_orientations)):
                raise ValueError("Mismatched goal lists: objects, targets, and orientations are not the same length.")
            self.get_logger().info(f"Received {len(objects_to_move)} objects to process.")   
            all_steps_succeeded = True
            
            for i, (obj, target, orientation) in enumerate(zip(objects_to_move, target_positions, target_orientations)):
            
                self.get_logger().info(f"--- Processing Object {i+1} / {len(objects_to_move)} ---")
                feedback_callback(f"Starting to process object {i+1} of {len(objects_to_move)}")
                
                feedback = ProcessWorkspace.Feedback()
                feedback.current_state = f"Processing object {i+1}"
                feedback.current_object = obj
                goal_handle.publish_feedback(feedback)
                
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
                        command_type="move",
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
                        command_type="move",
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
                        command_type="move",
                        coords=[target.x, target.y, 70.0, RX_DOWN, RY_DOWN, float(orientation)],
                        speed=100
                    ), "move to above place position (Z=70, RZ=User)"),

                    # 10. DESCEND TO PLACE POSITION (Z=30)
                    (SimpleCommandsAction.Goal(
                        command_type="move",
                        coords=[target.x, target.y, 30.0, RX_DOWN, RY_DOWN, float(orientation)],
                        speed=50
                    ), "descend to final placement height (Z=30)"),

                    # 11. DEACTIVATE VACUUM
                    (SimpleCommandsAction.Goal(
                        command_type="vacuum_off",
                    ), "deactivate vacuum"),

                    # 12. LIFT UP (Z=70)
                    (SimpleCommandsAction.Goal(
                        command_type="move",
                        coords=[target.x, target.y, 70.0, RX_DOWN, RY_DOWN, float(orientation)],
                        speed=DEFAULT_SPEED
                    ), "lift up after place (Z=70)"),

                    # 13. RGB: BLUE (Return to idle)
                    (SimpleCommandsAction.Goal(
                        command_type="set_rgb",
                        r=0, g=0, b=255
                    ), "set RGB to blue (done/idle)")
                ]
            

            for cmd, description in steps:
                # THIS IS THE SYNC CANCELLATION CHECK
                if goal_handle.is_cancel_requested:
                    feedback_callback("Sequence CANCELLED.")
                    all_steps_succeeded = False
                    sequence_message = "Action canceled by user."
                    break
                
                # This is the blocking call
                success, message = self._execute_primitive_step(
                    cmd, description, feedback_callback, goal_handle
                )
                
                if not success:
                    all_steps_succeeded = False
                    feedback_callback(f"ERROR: Step failed: {message}. Aborting all operations.")
                    break

                # *** NEW BLOCK FOR SLEEPING ***
                command_type = cmd.command_type
                if "move" in command_type:
                    self.get_logger().info("Post-move sleep: 4.0s")
                    time.sleep(4.0)
                elif "vacuum" in command_type:
                    self.get_logger().info("Post-vacuum sleep: 0.5s")
                    time.sleep(0.5)
                
                if not all_steps_succeeded:
                    break

            # --- End of logic ---
            
            if all_steps_succeeded:
                self.get_logger().info("Complex goal SUCCEEDED: All objects processed.")
                result.success = True
                result.message = "All objects processed successfully."
                goal_handle.succeed()
            else:
                self.get_logger().warn("Complex goal FAILED or CANCELED.")
                result.success = False
                result.message = "Operation failed or was canceled."
                goal_handle.abort()
                
        except Exception as e:
            self.get_logger().error(f"Unhandled exception in execute_callback: {e}")
            result.success = False
            result.message = f"An internal error occurred: {e}"
            goal_handle.abort()
            
        finally:
            # IMPORTANT: Reset the busy flag so new goals can be accepted
            with self.logic_lock:
                self.is_busy = False
                self.current_primitive_goal_handle = None
            self.get_logger().info("Execution finished. Reset to IDLE.")

        return result

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
