import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

import os
import math
import time
from math import sqrt
import RPi.GPIO as GPIO

from pymycobot import MyCobot, PI_PORT, PI_BAUD 

from sensor_msgs.msg import JointState
from std_msgs.msg import Header, String
from mycobot280pi_interfaces.msg import SimpleCommands, JointAnglesArray 

TOPIC_JOINT_ANGLES = '/robot/msg_joint_angles'
TOPIC_PRIMITIVE_COMMAND = '/planner/msg_primitive_command'


# ==================================================================
# ### HELPER CLASS: Vacuum Pump ###
# ==================================================================
class VacuumPumpV2Controller:
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
        self.feedback_pub = self.create_publisher(String, '/executor/system_service_feedback', 10)

        # Subscribers
        self.command_sub = self.create_subscription(
            SimpleCommands,
            TOPIC_PRIMITIVE_COMMAND,
            self.command_callback,
            10
        )

        self.joint_names = [
            "joint2_to_joint1", "joint3_to_joint2", "joint4_to_joint3",
            "joint5_to_joint4", "joint6_to_joint5", "joint6output_to_joint6"
        ]

        # Timer for publishing joint states
        self.status_timer = self.create_timer(1.0 / 30.0, self.publish_joint_states_callback)
        self.get_logger().info("MyCobot Driver Node ready (stateless).")

    # --- PUBLISHER CALLBACKS ---
    def publish_joint_states_callback(self):
        if not self.mc: return
        try:
            angles_degrees = self.mc.get_angles()
            if not angles_degrees or len(angles_degrees) != 6:
                self.get_logger().warn(f"GADAPET 6 WOY")
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

    # --- COMMAND HANDLER ---
    def command_callback(self, msg: SimpleCommands):
        if not self.mc:
            self.get_logger().error("MyCobot not connected.")
            self._publish_feedback("failure")
            return

        success = False
        try:
            if msg.command_type == "move":
                self.get_logger().warn(f"======== EXCUTOR move to {msg.coords}=====")
                self.mc.send_coords(list(msg.coords), msg.speed, 1)
                success = True
            elif msg.command_type == "move_joints":
                self.get_logger().warn(f"======== EXCUTOR move to {msg.coo}=====")
                self.mc.send_angles(list(msg.joint_angles), msg.speed)
                success = True
            elif msg.command_type == "vacuum_strong":
                self.get_logger().warn(f"======== EXCUTOR VACUUM STRONG =====")
                self.vacuum.vacuum_strong(); success = True
            elif msg.command_type == "vacuum_weak":
                self.get_logger().warn(f"======== EXCUTOR VACUUM weaG =====")
                self.vacuum.vacuum_weak(); success = True
            elif msg.command_type == "vacuum_off":
                self.get_logger().warn(f"======== EXCUTOR VACUUM ded =====")
                self.vacuum.vacuum_off(); success = True
            elif msg.command_type == "set_rgb":
                self.get_logger().warn(f"======== EXCUTOR VACUUM weaG =====")
                self.mc.set_color(msg.r, msg.g, msg.b); success = True
            else:
                self.get_logger().warn(f"Unknown command: {msg.command_type}")
        except Exception as e:
            self.get_logger().error(f" GAGAL WOY error: {e}")
            success = False

        self._publish_feedback("success" if success else "failure")

    def _publish_feedback(self, status: str):
        self.feedback_pub.publish(String(data=status))

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

