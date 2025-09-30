import rclpy
import threading
# asyncio is not needed for the synchronous approach
# import asyncio 

from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String
from rclpy.time import Time # Import Time for accurate time checks in the wait loop

# Define a safe timeout for blocking operations
WAIT_TIMEOUT = 5.0 # Increased timeout for safety

# Renamed topic for clarity
SERVICE_FEEDBACK_TOPIC = '/executor/system_service_feedback'

class PlannerLogic:
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
            callback_group=feedback_callback_group  
        )

    def set_command_publisher(self, pub):
        self.command_pub = pub

    def executor_feedback_callback(self, msg):
        self.node.get_logger().info(f"Received feedback from executor: '{msg.data}'")
        if msg.data == "success":
            self.feedback_event.set()


    def _send_and_wait_for_feedback_blocking(self, command_msg, goal_handle=None):
        """
        Sends a command and blocks the calling thread until:
        1. Successful feedback is received (unblocked by executor_feedback_callback).
        2. The global WAIT_TIMEOUT is reached.
        3. The ROS context shuts down (rclpy.ok() is False).
        4. (If goal_handle is provided) Cancellation is requested.
        """
        
        # 1. Clear the event and publish the command
        self.feedback_event.clear()
        
        if not self.command_pub:
            self.node.get_logger().error("Command publisher is not set!")
            return False
            
        self.command_pub.publish(command_msg)
        self.node.get_logger().info(f"Command '{command_msg.command_type}' sent. Waiting for feedback...")
        
        # 2. Block and check loop
        
        # Get start time using the clock for accurate timeout check
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
                
            # Wait for a small timeout, allowing the MultiThreadedExecutor to process callbacks
            is_set = self.feedback_event.wait(timeout=0.1) 
            
            if is_set:
                self.node.get_logger().info("Feedback received. Proceeding.")
                return True
        
        # This only happens if rclpy.ok() is False
        self.node.get_logger().warn("ROS context is shutting down while waiting.")
        return False


    # The rest of the class remains the same, but now uses the single, corrected
    # _send_and_wait_for_feedback_blocking function.
    
    def pick_and_place_object(self, obj, obj_target, obj_orientation, feedback_callback, goal_handle):
        self.node.get_logger().info(f"Starting pick and place for object ID: {obj.id}")
        self.state = "processing"
        
        plane_height = 50.0
        RX_DOWN = 180.0
        RY_DOWN = 0.0
        
        SPEED = 50

        try:
            # --- Step 1: Move to pick position ---
            feedback_callback(f"Moving to pick position for object {obj.id}")
            pick_pose = [obj.center_point.x, obj.center_point.y, plane_height, RX_DOWN, RY_DOWN, 0.0]
            cmd = SimpleCommands(command_type="move", coords=pick_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle):
                return False

            # --- Step 2: Activate vacuum ---
            feedback_callback("Activating vacuum")
            cmd = SimpleCommands(command_type="vacuum_on")
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle):
                return False

            # --- Step 3: Move to place position ---
            feedback_callback("Moving to place position")
            place_pose = [obj_target.x, obj_target.y, plane_height, RX_DOWN, RY_DOWN, float(obj_orientation)]
            cmd = SimpleCommands(command_type="move", coords=place_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle):
                return False

            # --- Step 4: Deactivate vacuum ---
            feedback_callback("Deactivating vacuum")
            cmd = SimpleCommands(command_type="vacuum_off")
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle):
                return False

            # --- Step 5: Return to home position ---
            feedback_callback("Returning to home position")
            home_pose = [135.0, 145.0, -30.0, 180.0, 0.0, 0.0]
            cmd = SimpleCommands(command_type="move", coords=home_pose, speed=SPEED)
            if not self._send_and_wait_for_feedback_blocking(cmd, goal_handle):
                return False

            self.state = "idle"
            feedback_callback(f"Finished processing object {obj.id}")
            
            return True # Return True to indicate success

        except Exception as e:
            self.node.get_logger().error(f"An exception occurred during PnP logic: {e}")
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
