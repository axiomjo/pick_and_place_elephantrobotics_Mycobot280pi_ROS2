import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor # Import executor here

import math
import time
import RPi.GPIO as GPIO 
from pymycobot import MyCobot, PI_PORT, PI_BAUD 

# Import handler modules
from .ren_publisher_joint_states_angles import StateAnglesPublisher
from .ren_service_server_simple_command import SimpleCommandServiceServer 
from .ren_action_server_command_primitive import PrimitivesActionServer 
from .ren_hardware_wrapper import MycobotHardwareWrapper 


class RobotExecutorNode(Node):
    """
    The main ROS 2 node. It acts as an orchestrator, delegating execution 
    to the hardware wrapper and communication to the handlers.
    """
    def __init__(self):
        super().__init__('robot_executor_node')
        
        # --- 1. CORE HARDWARE WRAPPER (Facade) ---
        self.hardware = MycobotHardwareWrapper(self.get_logger())
        
        # --- 2. Initialize ROS Components (Handlers) ---
        self.publisher = StateAnglesPublisher(self, self.hardware.get_joint_angles)
        self.service_server = SimpleCommandServiceServer(self, self.hardware.execute_command)
        self.action_server = PrimitivesActionServer(self, self.hardware.execute_command)

        self.get_logger().info("MyCobot Driver Node Orchestrator ready.")

    def cleanup_components(self):
        """Stops timers and cleans up all hardware connections."""
        self.get_logger().info("Cleaning up node components and hardware.")
        self.publisher.destroy() 
        self.hardware.cleanup_hardware() 

# ==================================================================
# ### ROS 2 ENTRY POINT (CONSOLIDATED) ###
# ==================================================================
def main(args=None):
    """ROS 2 Entry point. Creates the executor and spins the node."""
    rclpy.init(args=args)
    
    node = RobotExecutorNode()
    

    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    node.get_logger().info("Starting Consolidated MultiThreadedExecutor spin...")

    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt received. Shutting down.')
    finally:
        executor.shutdown()
        node.cleanup_components()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

