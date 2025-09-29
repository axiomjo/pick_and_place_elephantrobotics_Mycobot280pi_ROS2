# prn_planning_logic.py
import asyncio
import threading  # DIUBAH: Ganti asyncio.Event dengan threading.Event
from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String

class PlannerLogic:
    def __init__(self, node):
        self.node = node
        self.state = "idle"
        self.command_pub = None
        
        # DIUBAH: Gunakan Event yang thread-safe
        self.feedback_event = threading.Event()

        self.feedback_sub = self.node.create_subscription(
            String,
            '/executor/feedback',
            self.executor_feedback_callback,
            10)

    def set_command_publisher(self, pub):
        self.command_pub = pub

    def executor_feedback_callback(self, msg):
        self.node.get_logger().info(f"Received feedback from executor: '{msg.data}'")
        if msg.data == "success":
            # .set() pada threading.Event aman dipanggil dari thread manapun
            self.feedback_event.set()
            
    def _send_and_wait_for_feedback_blocking(self, command_msg):
        self.feedback_event.clear()
        self.command_pub.publish(command_msg)
        self.node.get_logger().info(f"Command '{command_msg.command_type}' sent. Waiting for feedback...")
        
        # Ini akan memblokir thread saat ini sampai event diset
        self.feedback_event.wait()
        self.node.get_logger().info("Feedback received. Proceeding.")

    
    def pick_and_place_object(self, obj, obj_target, obj_orientation, feedback_callback):
        self.node.get_logger().info(f"Starting pick and place for object ID: {obj.id}")
        self.state = "processing"
        
        plane_height = 50 #mm from robot's z=0
        RX_DOWN = 0.0 #klo mau posenya ke bawah
        RY_DOWN = 0.0 #klo mau posenya ke bawah


        # --- Langkah 1: Bergerak ke posisi pick ---
        feedback_callback("moving_to_pick")
        pick_pose = [obj.center_point.x, obj.center_point.y, plane_height, RX_DOWN, RY_DOWN, 0.0]
        cmd = SimpleCommands(command_type="move", coords=pick_pose, speed=50)
        self._send_and_wait_for_feedback_blocking(cmd)

        # --- Langkah 2: Aktifkan vacuum ---
        feedback_callback("activating_vacuum")
        cmd = SimpleCommands(command_type="vacuum_on")
        self._send_and_wait_for_feedback_blocking(cmd)

        # --- Langkah 3: Bergerak ke posisi place ---
        feedback_callback("moving_to_place")
        place_pose = [
            obj_target.x,
            obj_target.y,
            plane_height,
            RX_DOWN,  # Rx (Roll)
            RY_DOWN,  # Ry (Pitch)
            float(obj_orientation) # Rz (Yaw)
        ]
        cmd = SimpleCommands(command_type="move", coords=place_pose, speed=50)
        self._send_and_wait_for_feedback_blocking(cmd)

        feedback_callback("deactivating_vacuum")
        cmd = SimpleCommands(command_type="vacuum_off")
        self._send_and_wait_for_feedback_blocking(cmd)

        feedback_callback("returning_home")
        home_pose = [0.0, 0.1, 0.2, 0.0, 0.0, 0.0] #kudu ganti yg joint angles tea.
        cmd = SimpleCommands(command_type="move", coords=home_pose, speed=50)
        self._send_and_wait_for_feedback_blocking(cmd)

        self.state = "idle"
        feedback_callback("Done")
    

    def manual_command_callback(self, msg):
        self.node.get_logger().info(f"Forwarding manual command: {msg.command_type}")
        if self.command_pub:
            self.command_pub.publish(msg)
        else:
            self.node.get_logger().warn("Command publisher not set!")

    def detected_objects_callback(self, msg):
        num_objects = len(msg.objects)
        if num_objects > 0:
            ids = [str(obj.id) for obj in msg.objects]
            self.node.get_logger().info(f"Vision detected {num_objects} object(s): {', '.join(ids)}")
