# prn_main_ros_node.py

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor 
from rclpy.callback_groups import ReentrantCallbackGroup

from mycobot280pi_interfaces.msg import ManyDetectedObjects, SimpleCommands

from .prn_planning_logic import PlannerLogic
from .prn_action_server import PlannerActionServer
#from .prn_service_server import PlannerServiceServer

class PlannerRobotNode(Node):
    def __init__(self):
        super().__init__('planner_robot_node')
        
        # Create a callback group that allows callbacks to run in parallel
        # This is the "multi-lane highway" for our action server.
        action_callback_group = ReentrantCallbackGroup()
        timer_callback_group = ReentrantCallbackGroup()



        # 1. Bangun Otak Perencana (Logic) terlebih dahulu
        self.logic = PlannerLogic(self)

        # 2. Bangun antarmuka komunikasi (server) dan berikan akses ke logic
        self.action_server = PlannerActionServer(self, self.logic, action_callback_group)
        # self.service_server = PlannerServiceServer(self, self.logic)

        # 3. Buat semua publisher dan subscriber yang dikelola oleh node ini
        
        # Subscriber untuk objek terdeteksi dari pipeline visi
        self.create_subscription(
            ManyDetectedObjects,
            '/vision/detected_objects',
            self.logic.detected_objects_callback,
            10
        )

        # Subscriber untuk perintah manual sederhana dari GUI
        self.create_subscription(
            SimpleCommands,
            '/planner/manual_commands',
            self.logic.manual_command_callback,
            10
        )

        # Publisher untuk mengirimkan perintah primitif ke executor
        self.command_pub = self.create_publisher(
            SimpleCommands,
            '/planner/msg_primitive_command', # -> Nama topik yang benar
            10
        )
        
        self.logic.set_command_publisher(self.command_pub)

        
        self.get_logger().info("PlannerRobotNode is up and running. 🧠")
        
    
def main(args=None):
    rclpy.init(args=args)
    node = PlannerRobotNode()
    
    # -> Gunakan MultiThreadedExecutor untuk menangani async callbacks dengan baik
    #    Ini penting agar service, action, dan subscriber bisa berjalan bersamaan tanpa memblokir
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
