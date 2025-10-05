# roscomm/handlers/grcn_service_client_handler.py

import rclpy
from rclpy.node import Node
from rclpy.task import Future
# Import the specific service type
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure 
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from PyQt5.QtCore import QObject # Used for the facade type hint

ACTION_COMMAND_PRIMITIVES = '/gui/act_command_primitives'
class ServiceClientHandler:
    """
    Manages the single ROS 2 Service Client connection for all simple commands:
    /planner/srv_simple_command (Type: Mycobot280PiSimpleCommandsMadeSure).
    
    This handler encapsulates the logic for building and sending the unified request.
    """
    
    def __init__(self, node_host: Node, facade_ref: QObject):
        """
        Initializes the service client using the provided host node and facade reference.
        """
        self.node = node_host
        self.facade = facade_ref
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        # Create the SINGLE Service Client
        self.simple_command_client = self.node.create_client(
            Mycobot280PiSimpleCommandsMadeSure,
            ACTION_COMMAND_PRIMITIVES,
            qos_profile=qos_profile
        )
        self.node.get_logger().info('Unified Simple Command Service Client created.')


    def call_simple_command(self, 
                            command_type: str, 
                            coords: list = None, 
                            joint_angles: list = None,
                            speed: int = 0, 
                            r: int = 0, 
                            g: int = 0, 
                            b: int = 0, 
                            vacuum_pin1_level: int = 0, 
                            vacuum_pin2_level: int = 0, 
                            extra_strings: list = None, 
                            extra_floats: list = None, 
                            extra_ints: list = None):
        """
        Builds and sends the request to the /planner/srv_simple_command service.
        This method is called by the ROSCommunication facade.
        """
        # Ensure non-None defaults for list fields
        def ensure_list(value):
            """Return [] if value is None, otherwise return value itself."""
            return [] if value is None else value

        # Always safe: never None
        coords = ensure_list(coords)
        joint_angles = ensure_list(joint_angles)
        extra_strings = ensure_list(extra_strings)
        extra_floats = ensure_list(extra_floats)
        extra_ints = ensure_list(extra_ints)
        
        # 2. Build the request using the unified service type
        request = Mycobot280PiSimpleCommandsMadeSure.Request()
        
        # Core Command Type
        request.command_type = command_type
        
        # Movement Parameters
        request.coords = [float(c) for c in coords]
        request.joint_angles = [float(j) for j in joint_angles]
        request.speed = speed
        
        # RGB Parameters
        request.r = r
        request.g = g
        request.b = b
        
        # Vacuum Parameters
        request.vacuum_pin1_level = int(vacuum_pin1_level)
        request.vacuum_pin2_level = int(vacuum_pin2_level)
        
        # Extensibility Parameters
        request.extra_strings = extra_strings
        request.extra_floats = [float(f) for f in extra_floats]
        request.extra_ints = extra_ints
        
        self.node.get_logger().info(f'gui is calling service for: {command_type}')
        
        # 3. Call the service and attach the callback
        self.future = self.simple_command_client.call_async(request)
        self.future.add_done_callback(self._simple_command_response_callback)


    def _simple_command_response_callback(self, future: Future):
        """
        Callback executed by the ROS executor when the service response arrives.
        It routes the response back to the GUI via the facade's signal.
        """
        try:
            response = future.result()
            if response is not None:
                self.node.get_logger().info(
                    f"Command Response: Success={response.success}, Message='{response.message}'"
                )
                # Route the response back to the GUI via the facade's signal
                self.facade.simple_command_response_received.emit(response.success, response.message)
            else:
                error_msg = 'Service call failed or was interrupted (No result).'
                self.node.get_logger().error(error_msg)
                self.facade.simple_command_response_received.emit(False, error_msg)
                
        except Exception as e:
            error_msg = f'Service call exception: {e}'
            self.node.get_logger().error(error_msg)
            self.facade.simple_command_response.emit(False, error_msg)
