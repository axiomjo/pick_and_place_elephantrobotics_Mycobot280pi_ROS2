
# prn_service_server.py
import rclpy
from mycobot280pi_interfaces.srv import Mycobot280PiSetCoordsMadeSure
from mycobot280pi_interfaces.msg import SimpleCommands

class PlannerServiceServer:
    def __init__(self, node, logic):
        self.node = node
        self.logic = logic
        self.srv = node.create_service(
            Mycobot280PiSetCoordsMadeSure,
            '/planner/set_coords',
            self.handle_set_coords
        )

    def handle_set_coords(self, request, response):
        # Use planning logic to handle the move
        try:
            cmd = SimpleCommands()
            cmd.command_type = "move"
            cmd.coords = request.coords
            cmd.speed = request.speed
            self.logic.command_pub.publish(cmd)
            response.success = True
            response.message = "Move command sent to executor."
        except Exception as e:
            response.success = False
            response.message = f"Failed to send move command: {e}"
        return response
