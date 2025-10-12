"""
service_client_hdlr.py - Defines the ServiceClientHandler.

This handler encapsulates the logic for building and sending requests to the
unified simple command service.
"""
from rclpy.node import Node
from rclpy.task import Future
from PyQt5.QtCore import QObject
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

SERVICE_SIMPLE_COMMAND = '/gui/srv_simple_command'

class ServiceClientHandler:
    """Manages the ROS 2 Service Client for all simple commands."""
    
    def __init__(self, node_host, facade_ref): # (node_host: Node, facade_ref: QObject) -> None
        self.node = node_host
        self.facade = facade_ref
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        self.simple_command_client = self.node.create_client(
            Mycobot280PiSimpleCommandsMadeSure, SERVICE_SIMPLE_COMMAND, qos_profile=qos_profile
        )

    def call_simple_command(self, **kwargs):
        def ensure_list(value):
            return [] if value is None else value

        request = Mycobot280PiSimpleCommandsMadeSure.Request()
        request.command_type = kwargs.get('command_type', '')
        request.coords = [float(c) for c in ensure_list(kwargs.get('coords'))]
        request.joint_angles = [float(j) for j in ensure_list(kwargs.get('joint_angles'))]
        request.speed = kwargs.get('speed', 0)
        request.r, request.g, request.b = kwargs.get('r', 0), kwargs.get('g', 0), kwargs.get('b', 0)
        request.vacuum_pin1_level = int(kwargs.get('vacuum_pin1_level', 0))
        request.vacuum_pin2_level = int(kwargs.get('vacuum_pin2_level', 0))

        self.node.get_logger().info(f"GUI is calling service for: {request.command_type}")
        future = self.simple_command_client.call_async(request)
        future.add_done_callback(self._simple_command_response_callback)

    def _simple_command_response_callback(self, future): # (future: Future) -> None
        try:
            response = future.result()
            if response is not None:
                self.facade.simple_command_response_received.emit(response.success, response.message)
            else:
                self.facade.simple_command_response_received.emit(False, 'Service call failed (No result).')
        except Exception as e:
            self.facade.simple_command_response_received.emit(False, f'Service client call exception: {e}')
