# prn_robot_commander.py

import threading
import rclpy
from rclpy.node import Node

from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String

from . import prn_constants as const

class RobotCommander:
    """
    Handles low-level communication with the robot executor node.
    It provides a simple, blocking API for sending commands and waiting for completion.
    """
    def __init__(self, node: Node, feedback_callback_group):
        self.node = node
        self.feedback_event = threading.Event()

        # Publisher for sending commands to the executor
        self.command_pub = self.node.create_publisher(
            SimpleCommands,
            const.TOPIC_PRIMITIVE_COMMAND,
            10
        )

        # Subscriber for receiving feedback from the executor
        self.feedback_sub = self.node.create_subscription(
            String,
            const.TOPIC_EXECUTOR_FEEDBACK,
            self._executor_feedback_callback,
            10,
            callback_group=feedback_callback_group
        )
        self.node.get_logger().info("RobotCommander initialized.")

    def _executor_feedback_callback(self, msg):
        """Internal callback to set the event upon successful feedback."""
        self.node.get_logger().debug(f"Received feedback from executor: '{msg.data}'")
        if msg.data == "success":
            self.feedback_event.set()

    def _send_and_wait(self, command_msg: SimpleCommands, goal_handle=None):
        """
        The core blocking mechanism. Sends a command and waits for feedback.
        Also handles action cancellation checks.
        """
        self.feedback_event.clear()
        self.command_pub.publish(command_msg)
        self.node.get_logger().info(f"Command '{command_msg.command_type}' sent. Waiting for feedback...")

        start_time_sec = self.node.get_clock().now().nanoseconds / 1e9
        while rclpy.ok():
            elapsed_time_sec = (self.node.get_clock().now().nanoseconds / 1e9) - start_time_sec
            if elapsed_time_sec > const.WAIT_TIMEOUT_SEC:
                self.node.get_logger().warn(f"Wait for '{command_msg.command_type}' timed out.")
                return False

            if goal_handle and goal_handle.is_cancel_requested:
                self.node.get_logger().info("Cancellation detected while waiting for feedback.")
                return False

            if self.feedback_event.wait(timeout=0.1): # Wait with a timeout to be non-blocking for checks
                self.node.get_logger().info("Feedback 'success' received. Proceeding.")
                return True
        
        return False # rclpy is not ok

    # --- Public API for PlannerLogic ---

    def set_rgb(self, r, g, b):
        """Sends a non-blocking command to set the LED color."""
        color_cmd = SimpleCommands(command_type="set_rgb", r=r, g=g, b=b)
        self.command_pub.publish(color_cmd)
        return self._send_and_wait(color_cmd) 

    def move_to_pose(self, pose_coords: list, speed: int, goal_handle=None):
        cmd = SimpleCommands(command_type="move", coords=pose_coords, speed=speed)
        return self._send_and_wait(cmd, goal_handle)

    def set_vacuum(self, state: str, goal_handle=None):
        """
        Sets the vacuum state.
        :param state: Can be "strong" or "off".
        """
        if state not in ["strong", "off"]:
            self.node.get_logger().error(f"Invalid vacuum state requested: {state}")
            return False
        
        cmd = SimpleCommands(command_type=f"vacuum_{state}")
        return self._send_and_wait(cmd, goal_handle)
    
    def forward_simple_command(self, cmd: SimpleCommands):
        """Directly forwards a SimpleCommands message and waits for feedback."""
        return self._send_and_wait(cmd)
