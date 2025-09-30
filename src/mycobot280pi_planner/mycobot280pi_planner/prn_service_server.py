# prn_service_server.py

from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure
from mycobot280pi_interfaces.msg import SimpleCommands

from . import prn_constants as const # Use constants file

class PlannerServiceServer:
    def __init__(self, node, logic):
        self.node = node
        self.logic = logic # Logic now holds the commander
        self.srv = node.create_service(
            Mycobot280PiSimpleCommandsMadeSure,
            const.SERVICE_SIMPLE_COMMAND, # Use constant
            self.handle_simple_command  
        )
        self.node.get_logger().info("Service server for simple commands is ready.")

    def handle_simple_command(self, request, response):
        if self.logic.state != "idle":
            response.success = False
            response.message = "Planner is currently busy with another task."
            self.node.get_logger().warn("Rejected service call because planner is busy.")
            return response
            
        self.node.get_logger().info(f"Received service request: {request.command_type}")
        
        # Translate the service request into a SimpleCommands message.
        cmd = SimpleCommands(
            command_type=request.command_type,
            coords=request.coords,
            joint_angles=request.joint_angles,
            speed=request.speed,
            r=request.r, g=request.g, b=request.b,
            vacuum_pin1_level=request.vacuum_pin1_level,
            vacuum_pin2_level=request.vacuum_pin2_level
        )
        
        try:
            # --- REFACTORED: Use the commander's public method ---
            # The logic object holds the commander instance.
            success = self.logic.commander.forward_simple_command(cmd)
            
            if success:
                response.success = True
                response.message = f"Command '{cmd.command_type}' executed successfully."
            else:
                response.success = False
                response.message = f"Command '{cmd.command_type}' failed or timed out."
            
        except Exception as e:
            response.success = False
            response.message = f"An exception occurred: {e}"
            self.node.get_logger().error(f"Service call failed: {e}")

        return response
