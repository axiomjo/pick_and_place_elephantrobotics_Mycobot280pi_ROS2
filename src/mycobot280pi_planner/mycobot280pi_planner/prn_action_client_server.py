"""
# prn_action_client_server.py

all ros2 communication is built in this classes
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient, CancelResponse, GoalResponse
import asyncio

from mycobot280pi_interfaces.action import ProcessWorkspace, SimpleCommandsAction

from .prn_hsm_states import PlannerHSM, State


ACTION_COMPLEX_COMMAND = '/gui/act_complex_command'
ACTION_COMMAND_PRIMITIVES = '/planner/act_command_primitives' 

class PlannerNode(Node):
    def __init__(self):
        super().__init__('planner_node')
        self.get_logger().info("PlannerNode started.")
        
        self.hsm = PlannerHSM(self)
        
        self.simple_cmd_client = ActionClient(
            self, 
            action_type=SimpleCommandsAction, 
            action_name=ACTION_COMMAND_PRIMITIVES
        )
        
        if not self.simple_cmd_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("SimpleCommandsAction server not available! Shutting down.")
            raise SystemExit("SimpleCommandsAction server not available")
            
        self.get_logger().info("SimpleCommandsAction client is ready.")
        
        self.process_ws_server = ActionServer(
            self,
            action_type=ProcessWorkspace,
            action_name=ACTION_COMPLEX_COMMAND,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            execute_callback=self.execute_callback 
        )
        
        self.current_simple_goal_handle = None
        
    def goal_callback(self, goal_request):
        """ method for receiving or rejecting complex command goal"""
        
        if self.hsm.is_busy():
            self.get_logger().warn("HSM is busy, new goal REJECTED.")
            return rclpy.action.GoalResponse.REJECT
        
        self.get_logger().info("New complex goal ACCEPTED.")
        return rclpy.action.GoalResponse.ACCEPT
        
    def cancel_callback(self, cancel_request):
        """ method for cancelling the command primitives """
        self.get_logger().warn("Received CANCEL request from GUI.")
        asyncio.create_task(self.hsm.handle_cancel_request())
        
        return CancelResponse.ACCEPT
        
    async def execute_callback(self, goal_handle):
        """ method for starting the accepted goal. actual planning done by HSM """
        result_message = await self.hsm.handle_new_goal(goal_handle)
        return result_message
        
    async def execute_simple_command(self, goal_msg):
        """ method for actually sending command primitives """
        
        self.get_logger().info(f"Sending simple command: {goal_msg.command_type}")
        
        try:
            send_goal_future = self.simple_cmd_client.send_goal_async(goal_msg)
            
            self.current_simple_goal_handle = await send_goal_future
            
            if not self.current_simple_goal_handle.accepted:
                self.current_simple_goal_handle = None
                raise RuntimeError(f"Simple command '{goal_msg.command_type}' was rejected.")
                
            get_result_future = self.current_simple_goal_handle.get_result_async()
            result_wrapper = await get_result_future
            result = result_wrapper.result
            
            self.current_simple_goal_handle = None
            
            if not result.success:
                raise RuntimeError(f"Simple command failed: {result.message}")
                
            self.get_logger().info(f"Simple command success: {goal_msg.command_type}")
            return result
            
        except asyncio.CancelledError:
            self.get_logger().warn(f"Wait for simple command '{goal_msg.command_type}' was cancelled.")
            raise
            
    async def cancel_current_simple_command(self):
        """ method for canceling the current command primitive"""
        if self.current_simple_goal_handle and self.current_simple_goal_handle.is_active:
            self.get_logger().warn("Rippling cancel to simple_commands_action...")
            cancel_future = self.current_simple_goal_handle.cancel_goal_async()
            await cancel_future
            self.get_logger().warn("Simple command cancel acknowledged.")
            
        self.current_simple_goal_handle = None
            
            
            
        
        
