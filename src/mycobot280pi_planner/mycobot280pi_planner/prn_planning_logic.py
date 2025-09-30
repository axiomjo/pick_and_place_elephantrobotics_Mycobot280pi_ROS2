import rclpy
import threading
import asyncio

from mycobot280pi_interfaces.msg import SimpleCommands
from std_msgs.msg import String

class PlannerLogic:
    def __init__(self, node):
        self.node = node
        self.state = "idle"
        self.command_pub = None
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
            self.feedback_event.set()


    def _send_and_wait_for_feedback_blocking(self, command_msg, goal_handle):
        """TUsed ONLY by the synchronous Action goal handling."""
        
        self.node.get_logger().error("--- RUNNING THE NEW NON-BLOCKING WAIT FUNCTION (For Action) ---")

        
        self.feedback_event.clear()
        self.command_pub.publish(command_msg)
        self.node.get_logger().info(f"Command '{command_msg.command_type}' sent. Waiting for feedback...")
        
        while rclpy.ok() and not self.feedback_event.is_set():
            if goal_handle.is_cancel_requested:
                self.node.get_logger().info("Cancellation detected while waiting for feedback.")
                return False
            self.feedback_event.wait(timeout=0.1)

        if self.feedback_event.is_set():
            self.node.get_logger().info("Feedback received. Proceeding.")
            return True
        else:
            return False

    # ---  Asynchronous Wait Function for Service Handling ---
    async def _send_and_wait_for_feedback_async(self, command_msg, goal_handle):
        """Used by the asynchronous Service call handling."""

        self.node.get_logger().error("--- RUNNING ASYNCHRONOUS WAIT FUNCTION (For Service) ---")
        
        self.feedback_event.clear()
        self.state = "processing" # Set state before publishing
        self.command_pub.publish(command_msg)
        self.node.get_logger().info(f"Command '{command_msg.command_type}' sent. Awaiting feedback...")

        # 1. Loop until the feedback event is set.
        while rclpy.ok() and not self.feedback_event.is_set():
            # 2. Use asyncio.sleep(0) to yield control back to the ROS executor
            #    This is the non-blocking equivalent of threading.Event.wait()
            await asyncio.sleep(0.01) # Yield to allow the executor to process callbacks

        self.state = "idle" # Reset state after command is complete
        return self.feedback_event.is_set()

    
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
