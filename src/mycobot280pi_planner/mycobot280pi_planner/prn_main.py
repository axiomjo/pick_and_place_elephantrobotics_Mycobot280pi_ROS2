# prn_main.py
import rclpy
from rclpy.executors import MultiThreadedExecutor
from .prn_action_client_server import PlannerNode

def main(args=None):
    """
    Main function to run the synchronous node with a MultiThreadedExecutor.
    """
    rclpy.init(args=args)
    
    planner_node = None
    executor = None
    
    try:
        planner_node = PlannerNode()
        
        # Use a MultiThreadedExecutor to handle callbacks in parallel.
        # This is essential for a blocking action server.
        executor = MultiThreadedExecutor()
        executor.add_node(planner_node)
        
        planner_node.get_logger().info("Spinning node with MultiThreadedExecutor...")
        executor.spin()
        
    except SystemExit:
        rclpy.logging.get_logger('prn_main').error("Node startup failed (e.g., action server not found).")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        rclpy.logging.get_logger('prn_main').error(f"Unhandled exception in main: {e}")
    finally:
        if executor:
            executor.shutdown()
        if planner_node:
            planner_node.destroy_node()
        rclpy.shutdown()
        print("ROS 2 shutdown complete.")

if __name__ == '__main__':
    main()
