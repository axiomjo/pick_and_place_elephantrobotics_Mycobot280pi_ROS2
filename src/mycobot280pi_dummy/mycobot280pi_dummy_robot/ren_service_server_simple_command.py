
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup 
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure 

SERVICE_SIMPLE_COMMAND = '/gui/srv_simple_command'

class SimpleCommandServiceServer:
    """
    Manages the Service Server interface for immediate, non-blocking commands 
    like vacuum control or RGB setting.
    It calls the core execution logic on the main node.
    """
    def __init__(self, node: Node, execute_command_callback):
        self.node = node
        # The method from the Orchestrator node to perform hardware actions
        self.execute_command_callback = execute_command_callback
        
        # Use a ReentrantCallbackGroup to ensure the service requests don't block
        # the timer or action execution if they happen to take a little longer.
        self.command_callback_group = ReentrantCallbackGroup() 

        # Service Server Setup (for Simple/GUI Commands)
        self.srv = self.node.create_service(
            Mycobot280PiSimpleCommandsMadeSure,
            SERVICE_SIMPLE_COMMAND, 
            self.handle_simple_command_service,
            callback_group=self.command_callback_group
        )
        self.node.get_logger().info(f"Simple Command Service Server '{SERVICE_SIMPLE_COMMAND}' ready.")

    def handle_simple_command_service(self, request, response):
        """Service server handler: Calls the execution logic on the main node."""
        self.node.get_logger().info(f"Received service request: {request.command_type}")
        
        # Call the execution logic provided by the main node
        success, message = self.execute_command_callback(
            command_type=request.command_type,
            coords=request.coords,
            joint_angles=request.joint_angles,
            speed=request.speed,
            r=request.r, g=request.g, b=request.b,
        )
        
        response.success = success
        response.message = message
        return response
