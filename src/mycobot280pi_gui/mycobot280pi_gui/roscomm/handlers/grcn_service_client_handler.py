
"""
Defines the ServiceClientHandler class.

This class encapsulates all logic for interacting with a specific ROS 2 Service Client.
Its single responsibility is to manage the lifecycle of a service call:
checking for availability, sending a request, and processing the response.
"""

import rclpy.node
from PyQt5.QtCore import QObject

# Import the specific service definition
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure

SERVICE_SIMPLE_COMMAND = '/planner/srv_simple_command'


class ServiceClientHandler:
    """Manages all interactions with the Mycobot280PiSimpleCommandsMadeSure service."""

    def __init__(self, node: rclpy.node.Node, facade: QObject):
        """
        Initializes the service client handler.
        
        Args:
            node: The ROSOrchestratorNode instance to create the client on.
            facade: The ROSCommunication facade instance to emit signals.
        """
        self._node = node
        self._facade = facade
        self._simple_cmd_client = self._node.create_client(
            Mycobot280PiSimpleCommandsMadeSure,
            SERVICE_SIMPLE_COMMAND
        )

    def call_simple_command(self, coords, speed, is_linear_mode):
        """
        Constructs and sends a request to the simple command service.
        """
        if not self._simple_cmd_client.wait_for_service(timeout_sec=1.0):
            self._node.get_logger().warn(f"Service '{SERVICE_SIMPLE_COMMAND}' not available.")
            self._facade.simple_command_response.emit(False, 'Service not available')
            return
            
        # Construct the request message
        request = Mycobot280PiSimpleCommandsMadeSure.Request()
        request.coords = list(map(float, coords))
        request.speed = int(speed)
        request.is_linear_mode = bool(is_linear_mode)
        
        # Call the service asynchronously and add a callback for the response
        future = self._simple_cmd_client.call_async(request)
        future.add_done_callback(self._simple_command_done_callback)

    def _simple_command_done_callback(self, future):
        """
        Handles the response after the service call is complete.
        """
        try:
            response = future.result()
            self._facade.simple_command_response.emit(response.success, response.message)
        except Exception as e:
            self._node.get_logger().error(f"Service call failed with exception: {e}")
            self._facade.simple_command_response.emit(False, f'Exception during service call: {e}')
