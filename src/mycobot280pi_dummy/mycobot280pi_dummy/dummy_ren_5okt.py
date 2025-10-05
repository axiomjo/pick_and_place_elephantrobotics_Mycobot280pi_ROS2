import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup 
from rclpy.clock import Clock 

import os
import math
import time
from math import sqrt

# --- Conditional Import ---
# Attempt to import RPi.GPIO and pymycobot. Fallback to dummy classes if on non-Pi OS
try:
    import RPi.GPIO as GPIO
    from pymycobot import MyCobot, PI_PORT, PI_BAUD
    IS_HARDWARE_AVAILABLE = True
    print("--- INFO: Running with REAL hardware imports (RPi.GPIO and MyCobot) ---")
except (ImportError, RuntimeError):
    # ==================================================================
    # ### DUMMY IMPLEMENTATION FOR NON-PI / DESKTOP TESTING ###
    # ==================================================================
    class DummyMyCobot:
        """Placeholder for pymycobot.MyCobot"""
        def __init__(self, port, baud):
            print(f"*** DUMMY MYCOBOT: Initializing on port {port}, baud {baud}")
            self.DUMMY_ANGLES = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            time.sleep(0.5) # Simulate connection delay

        def send_coords(self, coords, speed, mode):
            print(f"*** DUMMY MYCOBOT: mc.send_coords(coords={coords}, speed={speed}, mode={mode})")

        def send_angles(self, angles, speed):
            print(f"*** DUMMY MYCOBOT: mc.send_angles(angles={angles}, speed={speed})")
            self.DUMMY_ANGLES = angles # Update dummy internal state

        def get_angles(self):
            # Return slightly different angles for testing joint state publishing
            self.DUMMY_ANGLES = [a + 0.1 for a in self.DUMMY_ANGLES]
            return [a % 360 for a in self.DUMMY_ANGLES]

        def set_color(self, r, g, b):
            print(f"*** DUMMY MYCOBOT: mc.set_color(r={r}, g={g}, b={b})")
            
        def is_paused(self): return False
        # Add other necessary methods if the code uses them...
            

    class DummyGPIO:
        """Placeholder for RPi.GPIO"""
        BCM = 1
        OUT = 1
        def setmode(self, mode): print("*** DUMMY GPIO: setmode called")
        def setup(self, pin, mode): print(f"*** DUMMY GPIO: setup pin {pin}")
        def output(self, pin, state): print(f"*** DUMMY GPIO: output pin {pin}, state {state}")
        def cleanup(self, pins=None): print("*** DUMMY GPIO: cleanup called")
    
    # Set classes to dummies and connection info to None/Placeholder
    MyCobot = DummyMyCobot
    GPIO = DummyGPIO()
    PI_PORT = "/dev/ttyACM0" # Placeholder value
    PI_BAUD = 115200         # Placeholder value
    IS_HARDWARE_AVAILABLE = False
    print("--- WARNING: Running with DUMMY hardware classes for testing ---")
    
# --- ROS Imports ---
from sensor_msgs.msg import JointState
from std_msgs.msg import Header, String
from mycobot280pi_interfaces.msg import SimpleCommands, JointAnglesArray 
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure 
from mycobot280pi_interfaces.action import SimpleCommandsAction as CommandPrimitives

# --- ROS Topics and Services ---
TOPIC_JOINT_ANGLES = '/robot/msg_joint_angles'
ACTION_COMMAND_PRIMITIVES = '/planner/act_command_primitives' 
SERVICE_SIMPLE_COMMAND = '/planner/srv_simple_command' 


# ==================================================================
# ### HELPER CLASS: Vacuum Pump ###
# ==================================================================
class VacuumPumpV2Controller:
    def __init__(self, pin_pump=21, pin_vent=20, logger=None):
        self.pin_pump = pin_pump
        self.pin_vent = pin_vent
        self.logger = logger
        try:
            # Use the imported GPIO object (either real or dummy)
            if IS_HARDWARE_AVAILABLE:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.pin_pump, GPIO.OUT)
                GPIO.setup(self.pin_vent, GPIO.OUT)
            else:
                GPIO.setmode(GPIO.BCM) # Calls dummy setmode
                GPIO.setup(self.pin_pump, GPIO.OUT) # Calls dummy setup
                GPIO.setup(self.pin_vent, GPIO.OUT) # Calls dummy setup
                
            self.set_state(1, 1)  # Default off
        except Exception as e:
            if self.logger:
                self.logger.warn(f"GPIO setup failed: {e}")

    def set_state(self, state_pump, state_vent):
        try:
            # Use the imported GPIO object (either real or dummy)
            GPIO.output(self.pin_pump, state_pump)
            GPIO.output(self.pin_vent, state_vent)
            if self.logger:
                self.logger.info(f"Vacuum state: pump={state_pump}, vent={state_vent}")
        except Exception as e:
            if self.logger:
                self.logger.warn(f"Failed to set vacuum state: {e}")

    def vacuum_off(self): self.set_state(1, 1)
    # The dummy class will print the command, fulfilling the requirement
    def vacuum_strong(self): self.set_state(0, 1)
    def vacuum_weak(self): self.set_state(0, 0)

    def cleanup(self):
        try:
            # Use the imported GPIO object (either real or dummy)
            if IS_HARDWARE_AVAILABLE:
                GPIO.cleanup([self.pin_pump, self.pin_vent])
            else:
                GPIO.cleanup() # Call dummy cleanup
        except Exception:
            pass


# ==================================================================
# ### MAIN EXECUTOR NODE (stateless) ###
# ==================================================================
class MyCobotDriverNode(Node):
    def __init__(self):
        super().__init__('robot_executor_node')
        
        self.command_callback_group = ReentrantCallbackGroup() 

        # Connect to MyCobot (Uses DummyMyCobot if hardware is not available)
        try:
            self.get_logger().info(f"Connecting to MyCobot on port: {PI_PORT}, baud: {PI_BAUD}")
            # MyCobot here is either the real class or the Dummy class
            self.mc = MyCobot(PI_PORT, PI_BAUD)
        except Exception as e:
            self.get_logger().error(f"FATAL: Failed to connect to MyCobot: {e}")
            self.mc = None
        
        # Initialize Vacuum Controller (Uses DummyGPIO if hardware is not available)
        self.vacuum = VacuumPumpV2Controller(logger=self.get_logger())

        # Publishers
        self.joint_state_pub = self.create_publisher(JointState, "joint_states", 10)
        self.gui_pub = self.create_publisher(JointAnglesArray, TOPIC_JOINT_ANGLES, 10)

        # Action Server Setup
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

        # Service Server Setup
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

        self.status_timer = self.create_timer(1.0 / 30.0, self.publish_joint_states_callback)
        self.get_logger().info("MyCobot Driver Node ready (stateless).")

    # --- ACTION CALLBACKS (Unchanged Logic) ---
    def _goal_callback(self, goal_request):
        self.get_logger().info(f'Received new goal request: {goal_request.command_type}. Accepting.')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request. Allowing.')
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
                # This calls DummyMyCobot.send_coords, which prints the command
                self.mc.send_coords(list(coords), speed, 1)
                return True, "Move successful."
            elif command_type == "move_joints" and angles:
                logger.warn(f"======== EXECUTOR move_joints to {angles}=====")
                # This calls DummyMyCobot.send_angles, which prints the command
                self.mc.send_angles(list(angles), speed)
                return True, "Joint move successful."
            elif command_type == "vacuum_on":
                logger.warn(f"======== EXECUTOR VACUUM STRONG (ON) =====")
                # This calls VacuumPumpV2Controller.vacuum_strong, which calls GPIO.output (Dummy)
                self.vacuum.vacuum_strong()
                return True, "Vacuum ON successful."
            elif command_type == "vacuum_off":
                logger.warn(f"======== EXCUTOR VACUUM OFF =====")
                self.vacuum.vacuum_off()
                return True, "Vacuum OFF successful."
            elif command_type == "set_rgb":
                logger.warn(f"======== EXCUTOR SET RGB ({r},{g},{b}) =====")
                # This calls DummyMyCobot.set_color, which prints the command
                self.mc.set_color(r, g, b)
                return True, "Set RGB successful."
            else:
                return False, f"Unknown or incomplete command: {command_type}"
        except Exception as e:
            logger.error(f"Execution FAILED for {command_type}: {e}")
            return False, f"Execution FAILED: {e}"


    def execute_primitive_command_callback(self, goal_handle):
        command_request = goal_handle.request
        self.get_logger().info(f"Executing action goal: {command_request.command_type}...")
        
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


    # --- SERVICE HANDLER (Unchanged Logic) ---
    def handle_simple_command_service(self, request, response):
        self.get_logger().info(f"Received service request: {request.command_type}")
        
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


    # --- PUBLISHER CALLBACKS (Joint state now uses DummyMyCobot.get_angles) ---
    def publish_joint_states_callback(self):
        if not self.mc: return
        try:
            # Calls DummyMyCobot.get_angles or real mc.get_angles
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

    # --- CLEANUP (Calls DummyGPIO.cleanup) ---
    def cleanup_hardware(self):
        self.get_logger().info("Cleaning up hardware connections.")
        self.vacuum.cleanup()


def main(args=None):
    rclpy.init(args=args)
    node = MyCobotDriverNode()
    
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
