
# prn_planning_logic.py
from mycobot280pi_interfaces.msg import SimpleCommands

class PlannerLogic:
    def __init__(self, node):
        self.node = node
        self.state = "idle"
        self.current_goal = None
        self.command_pub = None

    def manual_command_callback(self, msg):
        """
        Callback for /planner/manual_commands topic.
        Receives SimpleCommands from the GUI and forwards them to the executor.
        """
        self.node.get_logger().info(f"Received manual command: {msg.command_type}")
        if self.command_pub:
            self.command_pub.publish(msg)
        else:
            self.node.get_logger().warn("Command publisher not set!")

    async def pick_and_place_object(self, obj, obj_target, target_orientation):
        """
        Async generator for pick-and-place of a single object.
        Yields feedback state strings for action server feedback.
        """
        # Move to pick position
        self.state = "move_to_pick"
        pick_pose = [obj.center_point.x, obj.center_point.y, 0.0, 0.0, 0.0, 0.0]  # Example, adjust as needed
        cmd = SimpleCommands()
        cmd.command_type = "move"
        cmd.coords = pick_pose
        cmd.speed = 50
        self.command_pub.publish(cmd)
        yield "Moving to pick position"
        await self._sleep_async(2.0)

        # Activate vacuum
        self.state = "activate_vacuum"
        cmd = SimpleCommands()
        cmd.command_type = "vacuum_on"
        self.command_pub.publish(cmd)
        yield "Activating vacuum"
        await self._sleep_async(1.0)

        # Move to place position
        self.state = "move_to_place"
        place_pose = [obj_target.x, obj_target.y, 0.0, 0.0, 0.0, 0.0]  # Example, adjust as needed
        cmd = SimpleCommands()
        cmd.command_type = "move"
        cmd.coords = place_pose
        cmd.speed = 50
        self.command_pub.publish(cmd)
        yield "Moving to place position"
        await self._sleep_async(2.0)

        # Deactivate vacuum
        self.state = "deactivate_vacuum"
        cmd = SimpleCommands()
        cmd.command_type = "vacuum_off"
        self.command_pub.publish(cmd)
        yield "Deactivating vacuum"
        await self._sleep_async(1.0)

        # Return home (optional)
        self.state = "return_home"
        home_pose = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # Example, adjust as needed
        cmd = SimpleCommands()
        cmd.command_type = "move"
        cmd.coords = home_pose
        cmd.speed = 50
        self.command_pub.publish(cmd)
        yield "Returning home"
        await self._sleep_async(2.0)

        self.state = "idle"
        yield "Done"

    async def _sleep_async(self, seconds):
        # Helper for async sleep in rclpy coroutines
        import asyncio
        await asyncio.sleep(seconds)

    def detected_objects_callback(self, msg):
        """
        Callback for /vision/detected_objects topic.
        Receives ManyDetectedObjects message from the vision pipeline.
        For now, just log the number of detected objects and their IDs.
        """
        num_objects = len(msg.objects)
        self.node.get_logger().info(f"Received {num_objects} detected objects.")
        if num_objects > 0:
            ids = [str(obj.id) for obj in msg.objects]
            self.node.get_logger().info(f"Object IDs: {', '.join(ids)}")
        else:
            self.node.get_logger().info("No objects detected.")

    def set_command_publisher(self, pub):
        self.command_pub = pub

    def start_pick_and_place(self, pick_pose, place_pose, home_pose):
        self.state = "move_to_pick"
        self.pick_pose = pick_pose
        self.place_pose = place_pose
        self.home_pose = home_pose
        self._next_step()

    def _next_step(self):
        if self.state == "move_to_pick":
            cmd = SimpleCommands()
            cmd.command_type = "move"
            cmd.coords = self.pick_pose
            cmd.speed = 50
            self.command_pub.publish(cmd)
            self.state = "activate_vacuum"
            # In real code, wait for feedback or timer before next step
            self.node.get_clock().call_later(2.0, self._next_step)
        elif self.state == "activate_vacuum":
            cmd = SimpleCommands()
            cmd.command_type = "vacuum_on"
            self.command_pub.publish(cmd)
            self.state = "move_to_place"
            self.node.get_clock().call_later(1.0, self._next_step)
        elif self.state == "move_to_place":
            cmd = SimpleCommands()
            cmd.command_type = "move"
            cmd.coords = self.place_pose
            cmd.speed = 50
            self.command_pub.publish(cmd)
            self.state = "deactivate_vacuum"
            self.node.get_clock().call_later(2.0, self._next_step)
        elif self.state == "deactivate_vacuum":
            cmd = SimpleCommands()
            cmd.command_type = "vacuum_off"
            self.command_pub.publish(cmd)
            self.state = "return_home"
            self.node.get_clock().call_later(1.0, self._next_step)
        elif self.state == "return_home":
            cmd = SimpleCommands()
            cmd.command_type = "move"
            cmd.coords = self.home_pose
            cmd.speed = 50
            self.command_pub.publish(cmd)
            self.state = "idle"
            self.node.get_logger().info("Pick-and-place sequence complete.")
        else:
            self.node.get_logger().warn(f"Unknown state: {self.state}")

    # You can add methods for error handling, feedback, and more complex tasks
