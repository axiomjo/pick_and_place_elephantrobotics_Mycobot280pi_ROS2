from .prn_service_server import PlannerServiceServer

# prn_service_server.py

import rclpy
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure
from mycobot280pi_interfaces.msg import SimpleCommands

SERVICE_SIMPLE_COMMAND = '/planner/srv_simple_command'


class PlannerServiceServer:
    def __init__(self, node, logic):
        self.node = node
        self.logic = logic

        self.srv = node.create_service(
            Mycobot280PiSimpleCommandsMadeSure,
            SERVICE_SIMPLE_COMMAND, 
            self.handle_simple_command
        )
        self.node.get_logger().info("Service server for simple commands is ready.")

    def handle_simple_command(self, request, response):
        """
        Directly forwards GUI commands to executor (no blocking, no busy check).
        """
        self.node.get_logger().info(f"Received service request: {request.command_type}")

        cmd = SimpleCommands()
        cmd.command_type = request.command_type
        cmd.coords = request.coords
        cmd.joint_angles = request.joint_angles 
        cmd.speed = request.speed
        cmd.r = request.r
        cmd.g = request.g
        cmd.b = request.b
        cmd.vacuum_pin1_level = request.vacuum_pin1_level
        cmd.vacuum_pin2_level = request.vacuum_pin2_level

        try:
            self.logic._publish_command(cmd, "from service")
            response.success = True
            response.message = f"Command '{cmd.command_type}' forwarded."
        except Exception as e:
            response.success = False
            response.message = f"Failed to forward command: {e}"
            self.node.get_logger().error(f"Service call failed: {e}")

        return response

