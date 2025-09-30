# ren_main_ros_node.py (Modified to be compatible with the planner)

import rclpy
from rclpy.node import Node
from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String # <-- IMPORT a String message for feedback
from .ren_mycobot_interface import MyCobotInterface
from .ren_robot_state_manager import RobotStateManager

# Define the feedback topic name to ensure it matches the planner
TOPIC_EXECUTOR_FEEDBACK = '/executor/system_service_feedback'

class RobotMycobotExecutorNode(Node):
    def __init__(self):
        super().__init__('robot_mycobot_executor_node')
        self.api = MyCobotInterface(self.get_logger())
        self.state_manager = RobotStateManager(self.get_logger())

        # --- NEW: Create the feedback publisher ---
        self.feedback_pub = self.create_publisher(String, TOPIC_EXECUTOR_FEEDBACK, 10)

        # Subscribe to atomic commands from the planner
        self.create_subscription(
            SimpleCommands,
            '/planner/msg_primitive_command', # Match the planner's topic name
            self.command_callback,
            10
        )
        self.get_logger().info("robot_mycobot_executor_node is ready and waiting for commands.")

    # --- NEW: Helper function to publish feedback ---
    def _publish_feedback(self, status: str):
        msg = String()
        msg.data = status
        self.feedback_pub.publish(msg)
        self.get_logger().info(f"Published feedback: '{status}'")

    def command_callback(self, msg: SimpleCommands):
        """
        Receives a SimpleCommands message, executes the action, and publishes feedback.
        """
        success = False
        try:
            self.get_logger().info(f"Executing command: {msg.command_type}")
            # NOTE: Your planner uses "vacuum_strong" not "vacuum_on"
            if msg.command_type == "move":
                self.api.move_to_coords(msg.coords, msg.speed)
                self.state_manager.set_state("moving")
            elif msg.command_type == "vacuum_strong":
                self.api.vacuum_strong()
                self.state_manager.set_state("vacuum_on")
            elif msg.command_type == "vacuum_off":
                self.api.vacuum_off()
                self.state_manager.set_state("vacuum_off")
            elif msg.command_type == "vacuum_weak":
                self.api.vacuum_weak()
                self.state_manager.set_state("vacuum_weak")
            elif msg.command_type == "set_rgb":
                self.api.set_rgb(msg.r, msg.g, msg.b)
                self.state_manager.set_state("set_rgb")
            else:
                self.get_logger().warn(f"Unknown command_type: {msg.command_type}")
                # We still publish feedback, but it will be 'failure'
                success = False
                # The 'try' block continues, so we need to set success here.
                # The final 'finally' block will handle the publishing.
                return # Exit early to avoid setting success=True below

            # If no exception was raised, the command is considered successful
            success = True

        except Exception as e:
            self.state_manager.set_error(str(e))
            success = False
        finally:
            # --- NEW: Publish feedback after every command attempt ---
            self._publish_feedback("success" if success else "failure")


def main(args=None):
    rclpy.init(args=args)
    node = RobotMycobotExecutorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
