# dummy_executor_node.py

import rclpy
from rclpy.node import Node
from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String

SERVICE_FEEDBACK_TOPIC = '/executor/system_service_feedback'

class DummyExecutorNode(Node):
    def __init__(self):
        super().__init__('dummy_executor_node')

        self.command_sub = self.create_subscription(
            SimpleCommands,
            '/planner/msg_primitive_command',
            self.command_callback,
            10)

        self.feedback_pub = self.create_publisher(
            String,
            SERVICE_FEEDBACK_TOPIC,
            10)

        self.is_busy = False
        self.work_timer = None 
        
        # Define the instantaneous command for clear logic
        self.INSTANTANEOUS_COMMANDS = ["set_rgb"]
        
        self.get_logger().info("Dummy Executor Node is running and ready for commands. 🤖")

    def send_instantaneous_feedback(self):
        """Helper to send feedback immediately for non-blocking commands."""
        feedback_msg = String()
        feedback_msg.data = "success"
        self.feedback_pub.publish(feedback_msg)
        self.get_logger().debug("Instant feedback sent.")


    def command_callback(self, msg: SimpleCommands):
        
        # 1. Handle instantaneous commands (set_rgb)
        if msg.command_type in self.INSTANTANEOUS_COMMANDS:
            self.get_logger().info(f"Executing instantaneous command: '{msg.command_type}'...")
            
            # --- Conceptual Hardware Execution ---
            # NOTE: In a real node, you would call self.mycobot.set_color(msg.r, msg.g, msg.b) here
            # Since this is a DUMMY, we just execute and send feedback immediately.
            
            self.send_instantaneous_feedback()
            return # Exit, DO NOT set busy state or start timer

        # 2. Handle long-running commands (move, vacuum)
        if self.is_busy:
            self.get_logger().warn(
                f"Received command '{msg.command_type}' while busy. Ignoring."
            )
            return

        self.is_busy = True
        self.get_logger().info(f"Executing command: '{msg.command_type}'...")

        simulation_time = 1.0
        if msg.command_type == "move":
            simulation_time = 2.0
        elif "vacuum" in msg.command_type:
            simulation_time = 1.0
        
        # Start timer for long-running task
        self.work_timer = self.create_timer(simulation_time, self.finish_work_callback)

    def finish_work_callback(self):
        if self.work_timer:
            self.work_timer.cancel()
        
        self.get_logger().info("Execution finished. Sending 'success' feedback.")
        
        feedback_msg = String()
        feedback_msg.data = "success"
        self.feedback_pub.publish(feedback_msg)

        self.is_busy = False

def main(args=None):
    rclpy.init(args=args)
    node = DummyExecutorNode()
    try:
        # NOTE: rclpy.spin() will use SingleThreadedExecutor by default here, 
        # which is sufficient for this dummy node logic.
        rclpy.spin(node) 
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
