import rclpy
import threading

from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String
from rclpy.time import Time 
from rclpy.callback_groups import ReentrantCallbackGroup # (For reference, imported in main node)

# Define constants
WAIT_TIMEOUT = 5.0 # Max time to wait for execution feedback
SERVICE_FEEDBACK_TOPIC = '/executor/system_service_feedback' # Ensure this matches the executor's publisher

class PlannerLogic:
    # NOTE: The __init__ signature here assumes the feedback_callback_group 
    # is passed from prn_main_ros_node.py
    def __init__(self, node, feedback_callback_group):
        self.node = node
        self.state = "idle"
        self.command_pub = None
        self.feedback_event = threading.Event()
        
        self.feedback_sub = self.node.create_subscription(
            String,
            SERVICE_FEEDBACK_TOPIC,
            self.executor_feedback_callback,
            10,
            # Assigning this subscription to its own group prevents deadlocks 
            # with the main service/action callbacks in the MTE.
            callback_group=feedback_callback_group 
        )

    def set_command_publisher(self, pub):
        self.command_pub = pub

    def executor_feedback_callback(self, msg):
        """Called when a command's execution result is received."""
        self.node.get_logger().info(f"Received feedback from executor: '{msg.data}'")
        if msg.data == "success":
            self.feedback_event.set()


    def _send_rgb_command(self, r, g, b):
        """Sends a primitive command to set the RGB color (non-blocking)."""
        color_cmd = SimpleCommands(command_type="set_rgb", r=r, g=g, b=b)
        
        if self.command_pub:
            self.command_pub.publish(color_cmd)
        else:
            self.node.get_logger().warn("Command publisher is not set! Cannot set LED color.")


    def _send_and_wait_for_feedback_blocking(self, command_msg, goal_handle=None):
        """
        Sends a command and blocks the calling thread until:
        1. Successful feedback is received (via threading.Event).
        2. The global WAIT_TIMEOUT is reached.
        """
        
        # 1. Clear the event and publish the command
        self.feedback_event.clear()
        
        if not self.command_pub:
            self.node.get_logger().error("Command publisher is not set!")
            return False
            
        self.command_pub.publish(command_msg)
        self.node.get_logger().info(f"Command '{command_msg.command_type}' sent. Waiting for feedback...")
        
        # 2. Block and check loop
        start_time_sec = self.node.get_clock().now().nanoseconds / 1e9

        while rclpy.ok():
            elapsed_time_sec = (self.node.get_clock().now().nanoseconds / 1e9) - start_time_sec

            if elapsed_time_sec > WAIT_TIMEOUT:
                self.node.get_logger().warn(f"Waiting for command '{command_msg.command_type}' timed out after {WAIT_TIMEOUT}s.")
                return False
            
            # Check for cancellation only if running inside an Action (goal_handle is provided)
            if goal_handle and goal_handle.is_cancel_requested:
                self.node.get_logger().info("Cancellation detected while waiting for feedback.")
                return False
                
            # Wait for a small timeout (0.1s), allowing the MTE to process callbacks
            is_set = self.feedback_event.wait(timeout=0.1) 
            
            if is_set:
                self.node.get_logger().info("Feedback received. Proceeding.")
                return True
        
        # This occurs if rclpy.ok() is False
        self.node.get_logger().warn("ROS context is shutting down while waiting.")
        return False


    def pick_and_place_object(self, obj, obj_target, obj_orientation, feedback_callback, goal_handle=None):
        self.node.get_logger().info(f"Starting pick and place for object ID: {obj.id}")
        self.state = "processing"
        
        # Define kinematic constants and clearance values
        PLANE_HEIGHT_CLEARANCE = 50.0  # Height for safe travel over the object/table
        PICK_HEIGHT_Z = 1.0            # Height to descend to for grasping
        RX_DOWN = 180.0                # Tool pitch (downward-facing)
        RY_DOWN = 0.0
        SPEED = 50
        
        # --- COLOR MAPPING ---
        COLOR_CLEARANCE = (0, 0, 255)      # Blue
        COLOR_APPROACH = (255, 165, 0)     # Orange
        COLOR_GRASP = (0, 255, 0)          # Green
        COLOR_RELEASE = (255, 0, 0)        # Red
        COLOR_HOME = (255, 255, 255)       # White (Idle)

        # Define common poses based on the object/target
        pick_clearance_pose = [obj.center_point.x, obj.center_point.y, PLANE_HEIGHT_CLEARANCE, RX_DOWN, RY_DOWN, 0.0]
        pick_grasp_pose = [obj.center_point.x, obj.center_point.y, PICK_HEIGHT_Z, RX_DOWN, RY_DOWN, 0.0]
        place_clearance_pose = [obj_target.x, obj_target.y, PLANE_HEIGHT_CLEARANCE, RX_DOWN, RY_DOWN, float(obj_orientation)]
        place_drop_pose = [obj_target.x, obj_target.y, PICK_HEIGHT_Z, RX_DOWN, RY_DOWN, float(obj_orientation)]
        home_pose = [135.0, 145.0, -30.0, 180.0, 0.0, 0.0]

        try:
            # --- PICKING SEQUENCE ---

            # 1. Move to Pick Clearance Position (Blue)
            self._send_rgb_command(*COLOR_CLEARANCE)
            feedback_callback(f"Moving to pick clearance position for object {obj.id}")
            cmd = SimpleCommands(command_type="move", coords=pick_clearance_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle): return False
            
            # 2. Descend to Grasp Position (Orange)
            self._send_rgb_command(*COLOR_APPROACH)
            feedback_callback("Descending to grasp position")
            cmd = SimpleCommands(command_type="move", coords=pick_grasp_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle): return False

            # 3. Activate strong vacuum (Green)
            self._send_rgb_command(*COLOR_GRASP)
            feedback_callback("Activating strong vacuum")
            cmd = SimpleCommands(command_type="vacuum_strong") # Uses specific command
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle): return False
            
            # 4. Lift up to Pick Clearance Position (Orange)
            self._send_rgb_command(*COLOR_APPROACH)
            feedback_callback("Lifting object to clearance height")
            cmd = SimpleCommands(command_type="move", coords=pick_clearance_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle): return False

            # --- PLACING SEQUENCE ---

            # 5. Move to Place Clearance Position (Blue)
            self._send_rgb_command(*COLOR_CLEARANCE)
            feedback_callback("Moving to place clearance position")
            cmd = SimpleCommands(command_type="move", coords=place_clearance_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle): return False
            
            # 6. Descend to Drop Position (Orange)
            self._send_rgb_command(*COLOR_APPROACH)
            feedback_callback("Descending to drop position")
            cmd = SimpleCommands(command_type="move", coords=place_drop_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle): return False

            # 7. Deactivate vacuum (Red)
            self._send_rgb_command(*COLOR_RELEASE)
            feedback_callback("Deactivating vacuum")
            cmd = SimpleCommands(command_type="vacuum_off") # Uses specific command
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle): return False
            
            # 8. Lift up to Place Clearance Position (Orange)
            self._send_rgb_command(*COLOR_APPROACH)
            feedback_callback("Lifting away from the placed object")
            cmd = SimpleCommands(command_type="move", coords=place_clearance_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle): return False

            # 9. Return to home position (White)
            self._send_rgb_command(*COLOR_HOME)
            feedback_callback("Returning to home position")
            cmd = SimpleCommands(command_type="move", coords=home_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle): return False

            self.state = "idle"
            feedback_callback(f"Finished processing object {obj.id}")
            
            return True # Return True to indicate success

        except Exception as e:
            self.node.get_logger().error(f"An exception occurred during PnP logic: {e}")
            self._send_rgb_command(255, 0, 0) # Flash Red on error
            self.state = "idle"
            return False # Return False to indicate failure      

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
