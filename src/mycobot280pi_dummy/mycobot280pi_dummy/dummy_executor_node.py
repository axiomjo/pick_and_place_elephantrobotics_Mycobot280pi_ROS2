# dummy_executor_node.py

import rclpy
from rclpy.node import Node
from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String

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
            '/executor/feedback',
            10)

        self.is_busy = False
        self.work_timer = None # BARU: Variabel untuk menyimpan objek timer
        
        self.get_logger().info("Dummy Executor Node is running and ready for commands. 🤖")

    def command_callback(self, msg: SimpleCommands):
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
        
        # DIUBAH: Buat timer tanpa argumen 'oneshot' dan simpan
        self.work_timer = self.create_timer(simulation_time, self.finish_work_callback)

    def finish_work_callback(self):
        # DIUBAH: Hal pertama yang dilakukan adalah membatalkan timer!
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
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
