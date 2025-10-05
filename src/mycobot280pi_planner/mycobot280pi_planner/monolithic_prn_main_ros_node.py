# planner_robot_node.py

import rclpy
import threading
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor 
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionServer, ActionClient, CancelResponse, GoalResponse
from rclpy.action.client import ClientGoalHandle

# NOTE: Placeholder imports for interfaces (You must define these in your ROS package)
# Assuming these are available from 'mycobot280pi_interfaces'
from mycobot280pi_interfaces.msg import ManyDetectedObjects, SimpleCommands
from mycobot280pi_interfaces.action import ProcessWorkspace
# NOTE: Placeholder for the new Primitive Command Action Interface
from mycobot280pi_interfaces.action import SimpleCommandsAction as CommandPrimitives


# ====================================================================
# --- 1. Constants ---
# ====================================================================

# --- ROS Topics and Services ---
TOPIC_PRIMITIVE_COMMAND = '/planner/msg_primitive_command'
TOPIC_EXECUTOR_FEEDBACK = '/executor/system_service_feedback'
ACTION_COMPLEX_COMMAND = '/planner/act_complex_command'
ACTION_COMMAND_PRIMITIVES = '/planner/act_command_primitives' # NEW Action Client

# --- Logic Constants ---
WAIT_TIMEOUT_SEC = 5.0 # Max time to wait for execution feedback

# --- Kinematic and Planning Constants ---
PLANE_HEIGHT_CLEARANCE = 100.0  # Height for safe travel over the object/table
PICK_HEIGHT_Z = 50.0            # Height to descend to for grasping
RX_DOWN = 180.0                 # Tool pitch (downward-facing)
RY_DOWN = 0.0
DEFAULT_SPEED = 50

# A default "home" pose for the robot
HOME_POSE = [135.0, 145.0, -30.0, 180.0, 0.0, 0.0]

# --- State Feedback Colors (R, G, B) ---
COLOR_CLEARANCE = (0, 0, 255)      
COLOR_APPROACH = (255, 165, 0)     
COLOR_GRASP = (0, 255, 0)          
COLOR_RELEASE = (255, 0, 0)        
COLOR_HOME = (255, 255, 255)       
COLOR_ERROR = (255, 0, 0)          


# ====================================================================
# --- 2. Primitive Action Client (prn_primitive_action_client.py logic) ---
# ====================================================================

class PrimitiveActionClient:
    def __init__(self, node, callback_group):
        self.node = node
        self._action_client = ActionClient(
            node, 
            CommandPrimitives, # Type: mycobot280pi_interfaces/action/SimpleCommandsAction
            ACTION_COMMAND_PRIMITIVES,
            callback_group=callback_group
        )
        self.node.get_logger().info("Primitive Action Client is ready.")

    def send_primitive_command(self, simple_cmd_msg):
        """
        Sends a primitive command as an action goal and waits for the result (blocking).
        :param simple_cmd_msg: A SimpleCommands object (or similar structure)
        :return: Tuple (success: bool, message: str)
        """
        self.node.get_logger().info(f"Waiting for primitive action server: {ACTION_COMMAND_PRIMITIVES}...")
        if not self._action_client.wait_for_server(timeout_sec=WAIT_TIMEOUT_SEC):
            return False, "Primitive Action Server not available."

        # Map SimpleCommands fields to the action goal (assuming the goal is similar)
        goal_msg = CommandPrimitives.Goal()
        goal_msg.command_type = simple_cmd_msg.command_type
        goal_msg.coords = simple_cmd_msg.coords
        goal_msg.joint_angles = simple_cmd_msg.joint_angles # Include for completeness
        goal_msg.speed = simple_cmd_msg.speed
        goal_msg.r = simple_cmd_msg.r
        goal_msg.g = simple_cmd_msg.g
        goal_msg.b = simple_cmd_msg.b
        goal_msg.vacuum_pin1_level = simple_cmd_msg.vacuum_pin1_level
        goal_msg.vacuum_pin2_level = simple_cmd_msg.vacuum_pin2_level

        self.node.get_logger().info(f"Sending primitive goal: {goal_msg.command_type}")
        
        # Send goal and wait for acceptance (synchronous call using rclpy Future)
        future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self.node, future)
        
        goal_handle: ClientGoalHandle = future.result()
        
        if not goal_handle.accepted:
            return False, "Primitive goal rejected by server."
            
        self.node.get_logger().info('Primitive goal accepted. Waiting for result...')

        # Wait for the final result
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self.node, result_future)
        
        result = result_future.result().result
        
        return result.success, result.message


# ====================================================================
# --- 3. Planning Logic (prn_planning_logic.py) ---
# ====================================================================

class PlannerLogic:
    def __init__(self, node, callback_group):
        self.node = node
        # Initialize the new primitive action client
        self.primitive_client = PrimitiveActionClient(self.node, callback_group)

    def _execute_primitive_step(self, cmd: SimpleCommands, description: str, feedback_callback):
        """Uses the action client to execute a primitive command and blocks until completion."""
        feedback_callback(f"Executing step: {description}")
        success, message = self.primitive_client.send_primitive_command(cmd)
        
        if not success:
            self.node.get_logger().error(f"Primitive command FAILED: {description}. Message: {message}")
            feedback_callback(f"ERROR: {description} failed. {message}")
        else:
            self.node.get_logger().info(f"Primitive command SUCCEEDED: {description}")
            
        return success

    def pick_and_place_object(self, obj, obj_target, obj_orientation, feedback_callback, goal_handle):
        """
        Blocking pick and place sequence, using action client for each primitive.
        Returns False immediately on failure or cancellation.
        """
        
        feedback_callback(f"Starting pick and place for object {obj.id}")
        
        # Helper to check for cancellation before each step
        def check_cancel():
            if goal_handle.is_cancel_requested:
                feedback_callback("Sequence CANCELLED.")
                return True
            return False

        # Define the sequence of primitive commands
        steps = [
            # 1. Move above pick position
            (SimpleCommands(
                command_type="move", coords=[obj.center_point.x, obj.center_point.y, PLANE_HEIGHT_CLEARANCE, RX_DOWN, RY_DOWN, 0.0], speed=DEFAULT_SPEED
            ), "move above pick position"),

            # 2. Descend to pick height
            (SimpleCommands(
                command_type="move", coords=[obj.center_point.x, obj.center_point.y, PICK_HEIGHT_Z, RX_DOWN, RY_DOWN, 0.0], speed=DEFAULT_SPEED
            ), "descend to pick position"),
            
            # 3. Activate vacuum
            (SimpleCommands(command_type="vacuum_on"), "activate vacuum"),

            # 4. Move above place position
            (SimpleCommands(
                command_type="move", coords=[obj_target.x, obj_target.y, PLANE_HEIGHT_CLEARANCE, RX_DOWN, RY_DOWN, float(obj_orientation)], speed=DEFAULT_SPEED
            ), "move above place position"),

            # 5. Descend to place height
            (SimpleCommands(
                command_type="move", coords=[obj_target.x, obj_target.y, PICK_HEIGHT_Z, RX_DOWN, RY_DOWN, float(obj_orientation)], speed=DEFAULT_SPEED
            ), "descend to place position"),
            
            # 6. Deactivate vacuum
            (SimpleCommands(command_type="vacuum_off"), "deactivate vacuum"),

            # 7. Return to home
            (SimpleCommands(command_type="move", coords=HOME_POSE, speed=DEFAULT_SPEED), "return to home position"),
        ]
        
        for cmd, description in steps:
            if check_cancel():
                # Note: The logic handles cancellation, but the executor must handle 
                # cancelling the current primitive action call if needed.
                # For simplicity here, we rely on the goal_handle.is_cancel_requested check.
                return False 
            if not self._execute_primitive_step(cmd, description, feedback_callback):
                return False # Failed, stop the sequence

        feedback_callback(f"Finished pick and place for object {obj.id}")
        return True # Sequence succeeded


# ====================================================================
# --- 4. Complex Action Server (prn_action_server.py) ---
# ====================================================================

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
        self.node.get_logger().info('Received cancel request. Allowing.')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        """Runs pick-and-place sequence for each object, waiting for each primitive command."""
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

            # Blocking call to pick-and-place sequence
            success = self.logic.pick_and_place_object(
                obj, target_positions[idx], target_orientations[idx],
                publish_feedback, goal_handle
            )
            
            if not success:
                # Sequence failed or was cancelled internally
                if goal_handle.is_cancel_requested:
                    result_msg.success = False
                    result_msg.message = "Action canceled by user during execution."
                    goal_handle.canceled()
                else:
                    result_msg.success = False
                    result_msg.message = f"Pick and place failed for object {obj.id}."
                    goal_handle.abort()
                return result_msg


        result_msg.success = True
        result_msg.message = "All pick-and-place sequences completed successfully."
        goal_handle.succeed()
        self.node.get_logger().info("Goal succeeded.")
        return result_msg


# ====================================================================
# --- 5. Main ROS Node (prn_main_ros_node.py) ---
# ====================================================================

class PlannerRobotNode(Node):
    def __init__(self):
        super().__init__('planner_robot_node')
        
        # Create ReentrantCallbackGroups for parallel processing
        action_callback_group = ReentrantCallbackGroup()
        # This group is used by both the PlannerLogic's PrimitiveActionClient
        # and the PlannerActionServer's feedback publisher.
        logic_client_callback_group = ReentrantCallbackGroup() 

        # 1. Initialize Planner Logic (Brain)
        self.logic = PlannerLogic(self, logic_client_callback_group) 

        # 2. Initialize Complex Action Server (GUI/High-Level Interface)
        self.action_server = PlannerActionServer(self, self.logic, action_callback_group)


        self.get_logger().info("PlannerRobotNode is up and running. 🧠")
        
    
def main(args=None):
    rclpy.init(args=args)
    node = PlannerRobotNode()
    
    # Use MultiThreadedExecutor to handle the action server and action client 
    # callbacks concurrently. This is essential for the blocking sequence.
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
