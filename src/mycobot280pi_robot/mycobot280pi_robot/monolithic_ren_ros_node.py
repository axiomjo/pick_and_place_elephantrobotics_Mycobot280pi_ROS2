import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup 
from rclpy.clock import Clock # ADDED for explicit clock usage

import os
import math
import time
from math import sqrt
import RPi.GPIO as GPIO

# NOTE: Since you are on a Pi, these are used for hardware connection
from pymycobot import MyCobot, PI_PORT, PI_BAUD 

from sensor_msgs.msg import JointState
from std_msgs.msg import Header, String
from mycobot280pi_interfaces.msg import SimpleCommands, JointAnglesArray 
# NOTE: Placeholder imports for interfaces (You must define these in your ROS package)
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure 
from mycobot280pi_interfaces.action import SimpleCommandsAction as CommandPrimitives

# --- ROS Topics and Services ---
TOPIC_JOINT_ANGLES = '/robot/msg_joint_angles'
SERVICE_SIMPLE_COMMAND = '/planner/srv_simple_command' # NEW
ACTION_COMMAND_PRIMITIVES = '/gui/act_command_primitives' # NEW


# ==================================================================
# ### HELPER CLASS: Vacuum Pump ###
# ==================================================================
class VacuumPumpV2Controller:
    # ... (VacuumPumpV2Controller remains unchanged) ...
    def __init__(self, pin_pump=21, pin_vent=20, logger=None):
        self.pin_pump = pin_pump
        self.pin_vent = pin_vent
        self.logger = logger
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin_pump, GPIO.OUT)
            GPIO.setup(self.pin_vent, GPIO.OUT)
            self.set_state(1, 1)  # Default off
        except Exception as e:
            if self.logger:
                self.logger.warn(f"GPIO setup failed (Are you on a Pi?): {e}")

    def set_state(self, state_pump, state_vent):
        try:
            GPIO.output(self.pin_pump, state_pump)
            GPIO.output(self.pin_vent, state_vent)
            if self.logger:
                self.logger.info(f"Vacuum state: pump={state_pump}, vent={state_vent}")
        except Exception as e:
            if self.logger:
                self.logger.warn(f"Failed to set vacuum state: {e}")

    def vacuum_off(self): self.set_state(1, 1)
    def vacuum_strong(self): self.set_state(0, 1)
    def vacuum_weak(self): self.set_state(0, 0)

    def cleanup(self):
        try:
            GPIO.cleanup([self.pin_pump, self.pin_vent])
        except Exception:
            pass


# ==================================================================
# ### MAIN EXECUTOR NODE (stateless) ###
# ==================================================================
class MyCobotDriverNode(Node):
    def __init__(self):
        super().__init__('robot_executor_node')
        
        # Create callback group for action/service execution
        self.command_callback_group = ReentrantCallbackGroup() 

        # Connect to MyCobot
        try:
            self.get_logger().info(f"Connecting to MyCobot on port: {PI_PORT}, baud: {PI_BAUD}")
            self.mc = MyCobot(PI_PORT, PI_BAUD)
        except Exception as e:
            self.get_logger().error(f"FATAL: Failed to connect to MyCobot: {e}")
            self.mc = None

        self.vacuum = VacuumPumpV2Controller(logger=self.get_logger())

        # Publishers
        self.joint_state_pub = self.create_publisher(JointState, "joint_states", 10)
        self.gui_pub = self.create_publisher(JointAnglesArray, TOPIC_JOINT_ANGLES, 10)
        # self.feedback_pub = self.create_publisher(String, '/executor/system_service_feedback', 10) # REMOVED (Feedback is now via Action)

        # Removed the SimpleCommands subscriber (it is now an Action Server)
        # self.command_sub = self.create_subscription(...)

        # Action Server Setup (New: for Planner)
        self._action_server = ActionServer(
            node=self,
            action_type=CommandPrimitives,
            action_name=ACTION_COMMAND_PRIMITIVES,
            execute_callback=self.execute_primitive_command_callback,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=self.command_callback_group
        )
        self.get_logger().info("Primitive Command Action Server ready.")

        # Service Server Setup (New: for Simple/GUI Commands)
        self.srv = self.create_service(
            Mycobot280PiSimpleCommandsMadeSure,
            SERVICE_SIMPLE_COMMAND, 
            self.handle_simple_command_service,
            callback_group=self.command_callback_group
        )
        self.get_logger().info("Simple Command Service Server ready.")


        self.joint_names = [
            "joint2_to_joint1", "joint3_to_joint2", "joint4_to_joint3",
            "joint5_to_joint4", "joint6_to_joint5", "joint6output_to_joint6"
        ]

        # Timer for publishing joint states (Callback group not strictly needed here)
        self.status_timer = self.create_timer(1.0 / 30.0, self.publish_joint_states_callback)
        self.get_logger().info("MyCobot Driver Node ready (stateless).")

    # --- ACTION CALLBACKS ---
    def _goal_callback(self, goal_request):
        """Always accept new goals (stateless executor)."""
        self.get_logger().info(f'Received new goal request: {goal_request.command_type}. Accepting.')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle):
        """Always allow cancellation."""
        self.get_logger().info('Received cancel request. Allowing.')
        # NOTE: You may want to implement logic to stop the current movement here
        return CancelResponse.ACCEPT
    
    def _execute_command_logic(self, command_type, coords=None, angles=None, speed=50, r=0, g=0, b=0, logger=None):
        """Core execution logic shared by Action and Service."""
        logger = logger or self.get_logger()
        if not self.mc:
            logger.error("MyCobot not connected.")
            return False, "MyCobot not connected."

        try:
            if command_type == "move" and coords:
                logger.warn(f"======== EXECUTOR move to {coords}=====")
                # NOTE: send_coords blocks until movement is complete
                self.mc.send_coords(list(coords), speed, 1)
                return True, "Move successful."
            elif command_type == "move_joints" and angles:
                logger.warn(f"======== EXECUTOR move_joints to {angles}=====")
                # NOTE: send_angles blocks until movement is complete
                self.mc.send_angles(list(angles), speed)
                return True, "Joint move successful."
            elif command_type == "vacuum_on":
                logger.warn(f"======== EXECUTOR VACUUM STRONG (ON) =====")
                self.vacuum.vacuum_strong()
                return True, "Vacuum ON successful."
            elif command_type == "vacuum_off":
                logger.warn(f"======== EXCUTOR VACUUM OFF =====")
                self.vacuum.vacuum_off()
                return True, "Vacuum OFF successful."
            elif command_type == "set_rgb":
                logger.warn(f"======== EXCUTOR SET RGB ({r},{g},{b}) =====")
                self.mc.set_color(r, g, b)
                return True, "Set RGB successful."
            else:
                return False, f"Unknown or incomplete command: {command_type}"
        except Exception as e:
            logger.error(f"Execution FAILED for {command_type}: {e}")
            return False, f"Execution FAILED: {e}"


    def execute_primitive_command_callback(self, goal_handle):
        """Action server execution runs in its own thread."""
        command_request = goal_handle.request
        self.get_logger().info(f"Executing action goal: {command_request.command_type}...")
        
        # Action execution logic (Blocking)
        success, message = self._execute_command_logic(
            command_type=command_request.command_type,
            coords=command_request.coords,
            angles=command_request.joint_angles,
            speed=command_request.speed,
            r=command_request.r, g=command_request.g, b=command_request.b
        )

        result_msg = CommandPrimitives.Result()
        
        if goal_handle.is_cancel_requested:
            goal_handle.canceled()
            result_msg.success = False
            result_msg.message = "Execution cancelled."
            return result_msg

        if success:
            goal_handle.succeed()
            self.get_logger().info(f"Action SUCCEEDED: {command_request.command_type}")
        else:
            goal_handle.abort()
            self.get_logger().error(f"Action FAILED: {command_request.command_type}. {message}")
            
        result_msg.success = success
        result_msg.message = message
        return result_msg


    # --- SERVICE HANDLER ---
    def handle_simple_command_service(self, request, response):
        """Service server handler (Direct, non-blocking if underlying call is fast)."""
        self.get_logger().info(f"Received service request: {request.command_type}")
        
        # Service execution logic (Blocking, but fast for simple commands like vacuum/RGB)
        success, message = self._execute_command_logic(
            command_type=request.command_type,
            coords=request.coords,
            angles=request.joint_angles,
            speed=request.speed,
            r=request.r, g=request.g, b=request.b
        )
        
        response.success = success
        response.message = message
        return response


    # --- PUBLISHER CALLBACKS (Unchanged) ---
    def publish_joint_states_callback(self):
        if not self.mc: return
        try:
            angles_degrees = self.mc.get_angles()
            if not angles_degrees or len(angles_degrees) != 6:
                self.get_logger().warn("Could not retrieve 6 joint angles.")
                return

            radians_list = [math.radians(a) for a in angles_degrees]
            joint_state_msg = JointState(
                header=Header(stamp=self.get_clock().now().to_msg()),
                name=self.joint_names,
                position=radians_list,
                velocity=[],
                effort=[]
            )
            self.joint_state_pub.publish(joint_state_msg)

            array_msg = JointAnglesArray(joint_angles=[float(a) for a in angles_degrees])
            self.gui_pub.publish(array_msg)
        except Exception as e:
            self.get_logger().warn(f"Failed publishing joint states: {e}")

    # --- CLEANUP ---
    def cleanup_hardware(self):
        self.get_logger().info("Cleaning up hardware connections.")
        self.vacuum.cleanup()


def main(args=None):
    rclpy.init(args=args)
    node = MyCobotDriverNode()
    
    # MultiThreadedExecutor is essential to run:
    # 1. Action Server execution (blocking robot moves)
    # 2. Service Server handling
    # 3. Timer-based joint state publishing
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.cleanup_hardware()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
