
# prn_planning_logic.py
from mycobot280pi_interfaces.msg import SimpleCommands

class PlannerLogic:
    def __init__(self, node):
        self.node = node
        self.state = "idle"
        self.current_goal = None
        self.command_pub = None

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
