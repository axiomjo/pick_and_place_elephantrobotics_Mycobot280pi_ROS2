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

    async def handle_simple_command(self, request, response):
        """
        Handles a simple, blocking command from the GUI.
        This function is async to allow it to await the feedback-driven logic.
        """
        if self.logic.state != "idle":
            response.success = False
            response.message = "Planner is currently busy with another task."
            self.node.get_logger().warn("Rejected service call because planner is busy.")
            return response
            
        self.node.get_logger().info(f"Received service request to move to: {request.command_type}")
        
         # 1. Translate the rich service request into a SimpleCommands message.
        #    This is now easy because the message fields match the request fields!
        cmd = SimpleCommands()
        
        cmd.command_type = request.command_type
        
        cmd.coords = request.coords
        cmd.joint_angles = request.joint_angles # Add joint_angles
        cmd.speed = request.speed
        
        cmd.r = request.r
        cmd.g = request.g
        cmd.b = request.b
        
        cmd.vacuum_pin1_level = request.vacuum_pin1_level
        cmd.vacuum_pin2_level = request.vacuum_pin2_level
        
        
        try:
            success = await self.logic._send_and_wait_for_feedback_async(cmd, None)
            
            if success:
                response.success = True
                response.message = f"Command '{cmd.command_type}' executed and confirmed."
                self.node.get_logger().info(f"Service call for {cmd.command_type} successfully executed.")
            else:
                response.success = False
                response.message = f"Command '{cmd.command_type}' failed or was interrupted."
                self.node.get_logger().error(f"Service call for {cmd.command_type} failed.")
            
        except Exception as e:
            response.success = False
            response.message = f"Failed during service call execution: {e}"
            self.node.get_logger().error(f"Service call failed: {e}")

        return response
