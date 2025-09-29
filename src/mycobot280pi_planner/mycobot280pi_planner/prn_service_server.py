# prn_service_server.py
import rclpy
# -> Pastikan Anda mengimpor service type yang benar sesuai dokumentasi
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure
from mycobot280pi_interfaces.msg import SimpleCommands

class PlannerServiceServer:
    def __init__(self, node, logic):
        self.node = node
        self.logic = logic
        self.srv = node.create_service(
            Mycobot280PiSimpleCommandsMadeSure,
            '/planner/srv_simple_command', # -> Nama service yang benar
            self.handle_simple_command  # -> Arahkan ke async handler
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
            
        self.node.get_logger().info(f"Received service request to move to: {request.coords}")
        
        # -> 1. Terjemahkan service request menjadi sebuah SimpleCommands message.
        #    Service ini secara implisit adalah perintah "move".
        cmd = SimpleCommands()
        cmd.command_type = "move"
        cmd.coords = request.coords
        cmd.speed = request.speed
        
        try:
            # -> 2. Panggil dan tunggu metode logic yang sudah ada.
            #    Ini akan menjeda eksekusi di sini sampai feedback diterima.
            await self.logic._send_and_wait_for_feedback(cmd)
            
            # -> 3. Jika await selesai tanpa error, berarti berhasil.
            response.success = True
            response.message = "Move command executed and confirmed by executor."
            self.node.get_logger().info("Service call successfully executed.")
            
        except Exception as e:
            response.success = False
            response.message = f"Failed during service call execution: {e}"
            self.node.get_logger().error(f"Service call failed: {e}")

        return response
