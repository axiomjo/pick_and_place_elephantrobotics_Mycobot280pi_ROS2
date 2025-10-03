import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

import math
import time
from math import sqrt
import RPi.GPIO as GPIO

from pymycobot import MyCobot, PI_PORT, PI_BAUD

from sensor_msgs.msg import JointState
from std_msgs.msg import Header, String
from mycobot280pi_interfaces.msg import SimpleCommands


# ==================================================================
# ### KELAS HELPER DARI EXECUTOR NODE ###
# ==================================================================
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

    def vacuum_off(self): self.set_state(1, 1)
    def vacuum_strong(self): self.set_state(0, 1)
    def vacuum_weak(self): self.set_state(0, 0)
    def cleanup(self): GPIO.cleanup([self.pin_pump, self.pin_vent])

def in_position(target, current, tol=5.0):
    dx = target[0] - current[0]
    dy = target[1] - current[1]
    dz = target[2] - current[2]
    return sqrt(dx**2 + dy**2 + dz**2) < tol


# ==================================================================
# ### CLASS NODE GABUNGAN ###
# ==================================================================
class MyCobotDriverNode(Node):
    def __init__(self):
        super().__init__('mycobot_driver_node')
        self.state = "idle"
        self.error_msg = ""

        # ### SATU-SATUNYA KONEKSI KE HARDWARE ###
        # Inisialisasi MyCobot hanya satu kali di sini.
        try:
            self.get_logger().info(f"Connecting to MyCobot on port: {PI_PORT}, baud: {PI_BAUD}")
            self.mc = MyCobot(PI_PORT, PI_BAUD)
        except Exception as e:
            self.set_error(f"FATAL: Failed to connect to MyCobot: {e}")
            self.mc = None
        
        # Inisialisasi hardware lain (GPIO)
        self.vacuum = VacuumPumpV2Controller(logger=self.get_logger())

        # =======================================================
        # ### LOGIKA DARI JOINT PUBLISHER NODE ###
        # =======================================================
        self.joint_state_pub = self.create_publisher(JointState, "/robot/msg_joint_angle_states", 10)
        self.joint_names = [
            "joint2_to_joint1", "joint3_to_joint2", "joint4_to_joint3",
            "joint5_to_joint4", "joint6_to_joint5", "joint6output_to_joint6",
        ]
        # Timer untuk mem-publish status sendi secara periodik
        self.status_timer = self.create_timer(1.0 / 30.0, self.publish_joint_states_callback) # 30 Hz
        self.get_logger().info("Joint state publisher has been set up.")

        # =======================================================
        # ### LOGIKA DARI EXECUTOR NODE ###
        # =======================================================
        self.feedback_pub = self.create_publisher(String, '/executor/system_service_feedback', 10)
        self.command_sub = self.create_subscription(
            SimpleCommands, 
            '/planner/msg_primitive_command', 
            self.command_callback, 
            10
        )
        self.get_logger().info("Command executor has been set up.")
        self.get_logger().info("MyCobot Driver Node is ready.")

    # ------------------------------------------------------------------
    # --- METHOD DARI JOINT PUBLISHER ---
    # ------------------------------------------------------------------
    def publish_joint_states_callback(self):
        if not self.mc: return
        try:
            res = self.mc.get_angles()
            if not res or len(res) != 6:
                self.get_logger().debug("Invalid joint angles received. Skipping this cycle.")
                return

            radians_list = [math.radians(angle) for angle in res]
            joint_state_msg = JointState(
                header=Header(stamp=self.get_clock().now().to_msg()),
                name=self.joint_names,
                position=radians_list
            )
            self.joint_state_pub.publish(joint_state_msg)
        except Exception as e:
            self.get_logger().warn(f"Could not publish joint states: {e}")

    # ------------------------------------------------------------------
    # --- METHOD DARI EXECUTOR ---
    # ------------------------------------------------------------------
    def set_state(self, new_state):
        self.state = new_state
        self.get_logger().info(f"State -> {new_state}")

    def set_error(self, msg):
        self.state = "error"
        self.error_msg = msg
        self.get_logger().error(msg)
    
    def _publish_feedback(self, status: str):
        self.feedback_pub.publish(String(data=status))
        self.get_logger().info(f"Feedback: {status}")

    def move_to_coords(self, coords, speed, tol=5.0):
        # Fungsi blocking ini sekarang aman karena ada MultiThreadedExecutor
        if not self.mc: return False
        self.mc.send_coords(list(coords), speed, 1)
        while rclpy.ok():
            try:
                current = self.mc.get_coords()
                if current and in_position(coords, current, tol):
                    return True
                time.sleep(0.05)
            except Exception as e:
                self.get_logger().error(f"Move polling error: {e}")
                return False

    def set_rgb(self, r, g, b):
        if self.mc:
            self.mc.set_color(r, g, b)
            self.get_logger().info(f"RGB set to ({r},{g},{b})")




    def move_to_angles(self, angles_list, speed):
        if not self.mc: return False
        self.mc.send_angles(list(angles_list), speed)
        # Loop polling untuk menunggu gerakan selesai (mirip move_to_coords)
        while rclpy.ok():
            try:
                current = self.mc.get_angles()
                # Kita anggap selesai jika semua sendi berada dalam toleransi 1 derajat
                if current and all(abs(t - c) < 1.0 for t, c in zip(angles_list, current)):
                    return True
                time.sleep(0.05)
            except Exception as e:
                self.get_logger().error(f"Move angles polling error: {e}")
                return False
                
                
                
                
    def command_callback(self, msg: SimpleCommands):
        # Fungsi ini akan berjalan di thread-nya sendiri, tidak mengganggu publisher
        if not self.mc:
            self.get_logger().error("Cannot execute command, MyCobot not connected.")
            self._publish_feedback("failure")
            return

        success = False
        try:
            command_map = {
                "move": lambda: self.move_to_coords(msg.coords, msg.speed),
                "move_joints": lambda: self.move_to_angles(msg.coords, msg.speed),
                "vacuum_strong": self.vacuum.vacuum_strong,
                "vacuum_weak": self.vacuum.vacuum_weak,
                "vacuum_off": self.vacuum.vacuum_off,
                "set_rgb": lambda: self.set_rgb(msg.r, msg.g, msg.b)
            }

            if msg.command_type in command_map:
                self.set_state(f"executing_{msg.command_type}")
                result = command_map[msg.command_type]()
                success = result if isinstance(result, bool) else True
            else:
                self.get_logger().warn(f"Unknown command: {msg.command_type}")
                success = False
        except Exception as e:
            self.set_error(str(e))
            success = False
        finally:
            if self.state != "error":
                self.set_state("idle")
            self._publish_feedback("success" if success else "failure")

    def cleanup_hardware(self):
        """Dipanggil saat node dimatikan."""
        self.get_logger().info("Cleaning up hardware connections.")
        self.vacuum.cleanup()


def main(args=None):
    rclpy.init(args=args)
    node = MyCobotDriverNode()
    
    # ### PENTING: GUNAKAN MultiThreadedExecutor ###
    # Ini memungkinkan callback timer (untuk joint states) dan callback subscriber 
    # (untuk perintah) berjalan secara paralel di thread yang berbeda.
    # Jadi, `while` loop di `move_to_coords` tidak akan mem-blokir publisher joint state.
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
