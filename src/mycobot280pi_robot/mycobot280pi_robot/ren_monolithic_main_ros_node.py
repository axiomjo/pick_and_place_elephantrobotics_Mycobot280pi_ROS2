"""
monolithic_executor_node.py

A single-file ROS2 node that merges the responsibilities of state management,
hardware interfacing, and ROS communication. It listens for commands from a planner,
executes them using pymycobot, and provides feedback.
"""

import rclpy
from rclpy.node import Node
from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String
from pymycobot import MyCobot, PI_PORT, PI_BAUD
import RPi.GPIO as GPIO

# --- Helper Class from ren_mycobot_interface.py ---
# It's still good practice to keep this as a separate class within the file.
class VacuumPumpV2Controller:
    """
    Controls the Vacuum Pump V2.0 using two GPIO pins.
    """
    def __init__(self, pin_pump=21, pin_vent=20, logger=None):
        self.pin_pump = pin_pump
        self.pin_vent = pin_vent
        self.logger = logger
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_pump, GPIO.OUT)
        GPIO.setup(self.pin_vent, GPIO.OUT)
        self.set_state(1, 1)  # Default: Off

    def set_state(self, state_pump, state_vent):
        GPIO.output(self.pin_pump, state_pump)
        GPIO.output(self.pin_vent, state_vent)
        desc = self.describe_state(state_pump, state_vent)
        if self.logger:
            self.logger.info(f"Vacuum Pump set: PUMP={state_pump}, VENT={state_vent} ({desc})")

    def vacuum_off(self):
        self.set_state(1, 1)

    def vacuum_strong(self):
        self.set_state(0, 1)

    def vacuum_weak(self):
        self.set_state(0, 0)

    @staticmethod
    def describe_state(state_pump, state_vent):
        if state_pump == 1:
            return "Off"
        elif state_pump == 0 and state_vent == 1:
            return "Strong Vacuum"
        elif state_pump == 0 and state_vent == 0:
            return "Weak Vacuum"
        else:
            return "Unknown"

    def cleanup(self):
        GPIO.cleanup([self.pin_pump, self.pin_vent])


# --- Main Monolithic Node Class ---
class MonolithicExecutorNode(Node):
    def __init__(self):
        super().__init__('monolithic_executor_node')
        
        # --- Merged from RobotStateManager ---
        self.state = "idle"
        self.error_msg = ""
        # self.task_sequence and self.task_step were not used in the callback,
        # so they are omitted for this simpler version.

        # --- Merged from MyCobotInterface ---
        self.mc = None
        try:
            self.mc = MyCobot(PI_PORT, PI_BAUD)
            self.get_logger().info("Connected to MyCobot.")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to MyCobot: {e}")
            self.set_error(f"Failed to connect to MyCobot: {e}")

        # Initialize vacuum pump controller with configurable pins
        self.vacuum = VacuumPumpV2Controller(pin_pump=21, pin_vent=20, logger=self.get_logger())

        # --- From ren_main_ros_node.py & Previous Feedback Logic ---
        # Publisher for providing feedback to the planner
        self.feedback_pub = self.create_publisher(String, '/executor/system_service_feedback', 10)

        # Subscriber for receiving commands
        self.create_subscription(
            SimpleCommands,
            '/planner/msg_primitive_command', # Ensure topic name matches planner
            self.command_callback,
            10
        )
        self.get_logger().info("Monolithic executor node is ready and waiting for commands.")

    # --- Methods from RobotStateManager ---
    def set_state(self, new_state):
        self.state = new_state
        self.get_logger().info(f"Robot state updated to: {new_state}")

    def get_state(self):
        return self.state

    def set_error(self, msg):
        self.state = "error"
        self.error_msg = msg
        self.get_logger().error(f"Robot error: {msg}")

    def clear_error(self):
        self.state = "idle"
        self.error_msg = ""
        self.get_logger().info("Error cleared, state set to idle.")

    # --- Methods from MyCobotInterface ---
    def move_to_coords(self, coords, speed):
        if self.mc:
            self.get_logger().info(f"Moving to coords: {coords} at speed {speed}")
            self.mc.send_coords(list(coords), speed, 1) # Using mode 1 for joint interpolation

    def set_rgb(self, r, g, b):
        if self.mc:
            self.get_logger().info(f"Set RGB color to ({r}, {g}, {b})")
            self.mc.set_color(r, g, b)

    # --- Core ROS Logic ---
    def _publish_feedback(self, status: str):
        msg = String()
        msg.data = status
        self.feedback_pub.publish(msg)
        self.get_logger().info(f"Published feedback: '{status}'")

    def command_callback(self, msg: SimpleCommands):
        success = False
        try:
            # Check for error state first
            if self.get_state() == "error":
                self.get_logger().warn("Cannot execute command, in error state.")
                return

            self.get_logger().info(f"Executing command: {msg.command_type}")
            
            # Note: The planner sends "vacuum_strong", not "vacuum_on"
            if msg.command_type == "move":
                self.set_state("moving")
                self.move_to_coords(msg.coords, msg.speed)
            elif msg.command_type == "vacuum_strong":
                self.set_state("vacuum_on")
                self.vacuum.vacuum_strong() # Now calling the method on self.vacuum
            elif msg.command_type == "vacuum_off":
                self.set_state("vacuum_off")
                self.vacuum.vacuum_off()
            elif msg.command_type == "vacuum_weak":
                self.set_state("vacuum_weak")
                self.vacuum.vacuum_weak()
            elif msg.command_type == "set_rgb":
                self.set_state("set_rgb")
                self.set_rgb(msg.r, msg.g, msg.b)
            else:
                self.get_logger().warn(f"Unknown command_type: {msg.command_type}")
                success = False # Command is unknown, so it's a failure
                return # Exit early

            success = True

        except Exception as e:
            self.set_error(str(e))
            success = False
        finally:
            if self.get_state() != "error":
                self.set_state("idle")
            # Publish feedback after every command attempt
            self._publish_feedback("success" if success else "failure")
            
    def cleanup_hardware(self):
        self.get_logger().info("Cleaning up GPIO resources.")
        self.vacuum.cleanup()

def main(args=None):
    rclpy.init(args=args)
    node = MonolithicExecutorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cleanup_hardware()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
