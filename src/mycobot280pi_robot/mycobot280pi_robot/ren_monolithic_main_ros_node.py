import rclpy
from rclpy.node import Node
from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String
from pymycobot import MyCobot, PI_PORT, PI_BAUD
import RPi.GPIO as GPIO
from math import sqrt
import time

class VacuumPumpV2Controller:
    def __init__(self, pin_pump=21, pin_vent=20, logger=None):
        self.pin_pump = pin_pump
        self.pin_vent = pin_vent
        self.logger = logger
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_pump, GPIO.OUT)
        GPIO.setup(self.pin_vent, GPIO.OUT)
        self.set_state(1, 1)  # Default off

    def set_state(self, state_pump, state_vent):
        GPIO.output(self.pin_pump, state_pump)
        GPIO.output(self.pin_vent, state_vent)
        if self.logger:
            self.logger.info(f"Vacuum state: pump={state_pump}, vent={state_vent}")

    def vacuum_off(self):
        self.set_state(1, 1)
    def vacuum_strong(self):
        self.set_state(0, 1)
    def vacuum_weak(self):
        self.set_state(0, 0)
    def cleanup(self):
        GPIO.cleanup([self.pin_pump, self.pin_vent])

def in_position(target, current, tol=5.0):
    dx = target[0] - current[0]
    dy = target[1] - current[1]
    dz = target[2] - current[2]
    return sqrt(dx**2 + dy**2 + dz**2) < tol

class MonolithicExecutorNode(Node):
    def __init__(self):
        super().__init__('monolithic_executor_node')
        self.state = "idle"
        self.error_msg = ""

        # Robot connection
        try:
            self.mc = MyCobot(PI_PORT, PI_BAUD)
            self.get_logger().info("Connected to MyCobot.")
        except Exception as e:
            self.set_error(f"Failed to connect to MyCobot: {e}")
            self.mc = None

        self.vacuum = VacuumPumpV2Controller(logger=self.get_logger())

        # ROS comms
        self.feedback_pub = self.create_publisher(String, '/executor/system_service_feedback', 10)
        self.create_subscription(SimpleCommands, '/planner/msg_primitive_command', self.command_callback, 10)
        self.get_logger().info("Executor ready.")

    def set_state(self, new_state):
        self.state = new_state
        self.get_logger().info(f"State -> {new_state}")

    def get_state(self):
        return self.state

    def set_error(self, msg):
        self.state = "error"
        self.error_msg = msg
        self.get_logger().error(msg)

    def clear_error(self):
        self.state = "idle"
        self.error_msg = ""

    def _publish_feedback(self, status: str):
        msg = String()
        msg.data = status
        self.feedback_pub.publish(msg)
        self.get_logger().info(f"Feedback: {status}")

    # --- Non-blocking move with polling ---
    def move_to_coords(self, coords, speed, tol=5.0):
        if not self.mc:
            self.get_logger().warn("No MyCobot connected.")
            return False
        self.mc.send_coords(list(coords), speed, 1)  # mode 1: joint interpolation

        """
        
        BUTUH CARA LEBIH BAIK DARIPADA BLOCKING GINI
        # Poll until robot reaches target
        while rclpy.ok():
            try:
                current = self.mc.get_coords()
                if current and in_position(coords, current, tol):
                    return True
                time.sleep(0.05)
            except Exception as e:
                self.get_logger().error(f"Move polling error: {e}")
                return False
        """
        
        
    def set_rgb(self, r, g, b):
        if self.mc:
            self.mc.set_color(r, g, b)
            self.get_logger().info(f"RGB set to ({r},{g},{b})")

    def command_callback(self, msg: SimpleCommands):
        success = False
        try:
            if self.state == "error":
                self.get_logger().warn("Cannot execute command: error state.")
                return

            if msg.command_type == "move":
                self.set_state("moving")
                success = self.move_to_coords(msg.coords, msg.speed)
            elif msg.command_type == "vacuum_strong":
                self.set_state("vacuum_on")
                self.vacuum.vacuum_strong()
                success = True
            elif msg.command_type == "vacuum_off":
                self.set_state("vacuum_off")
                self.vacuum.vacuum_off()
                success = True
            elif msg.command_type == "vacuum_weak":
                self.set_state("vacuum_weak")
                self.vacuum.vacuum_weak()
                success = True
            elif msg.command_type == "set_rgb":
                self.set_state("set_rgb")
                self.set_rgb(msg.r, msg.g, msg.b)
                success = True
            else:
                self.get_logger().warn(f"Unknown command: {msg.command_type}")
                success = False
                return

        except Exception as e:
            self.set_error(str(e))
            success = False
        finally:
            if self.state != "error":
                self.set_state("idle")
            self._publish_feedback("success" if success else "failure")

    def cleanup_hardware(self):
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

