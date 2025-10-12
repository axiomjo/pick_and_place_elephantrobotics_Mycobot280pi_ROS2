"""
action_client_hdlr.py - Defines the ActionClientHandler.

This class encapsulates all logic for interacting with the complex command
ROS 2 Action Client.
"""
import rclpy.node
from PyQt5.QtCore import QObject
from rclpy.action import ActionClient
import threading
from mycobot280pi_interfaces.action import ProcessWorkspace
from action_msgs.msg import GoalStatus

ACTION_COMPLEX_COMMAND = '/planner/act_complex_command'

class ActionClientHandler:
    """Manages all interactions with the ProcessWorkspace action client."""

    def __init__(self, node, facade): # (node: rclpy.node.Node, facade: QObject) -> None
        self._node = node
        self._facade = facade
        self._action_client = ActionClient(node, ProcessWorkspace, ACTION_COMPLEX_COMMAND)
        self._goal_handle_lock = threading.Lock()
        self._active_goal_handle = None

    def send_goal(self, objects_to_move, target_positions, target_orientation):
        if not self._action_client.wait_for_server(timeout_sec=2.0):
            self._node.get_logger().error('Action server not available!')
            self._facade.action_result.emit(False, 'Action server not available')
            return
            
        goal_msg = ProcessWorkspace.Goal()
        goal_msg.objects_to_move = objects_to_move
        goal_msg.objects_target_position = target_positions
        goal_msg.objects_target_orientation = target_orientation
        
        self._node.get_logger().info('Sending complex action goal...')
        send_goal_future = self._action_client.send_goal_async(goal_msg, feedback_callback=self._feedback_callback)
        send_goal_future.add_done_callback(self._goal_response_callback)

    def cancel_goal(self):
        with self._goal_handle_lock:
            if self._active_goal_handle is None: return
            status = self._active_goal_handle.status
            if status in [GoalStatus.STATUS_ACCEPTED, GoalStatus.STATUS_EXECUTING]:
                self._node.get_logger().info('Cancelling the active goal...')
                self._active_goal_handle.cancel_goal_async()

    def _goal_response_callback(self, future):
        goal_handle = future.result() 
        if not goal_handle.accepted:
            self._facade.action_result.emit(False, 'Goal rejected')
            return
        with self._goal_handle_lock:
            self._active_goal_handle = goal_handle
        goal_handle.get_result_async().add_done_callback(self._result_callback)

    def _feedback_callback(self, feedback_msg):
        self._facade.action_feedback.emit(feedback_msg.feedback.current_state)

    def _result_callback(self, future):
        try:
            result = future.result().result
            self._facade.action_result.emit(result.success, result.message)
        except Exception as e:
            self._facade.action_result.emit(False, f'Exception: {e}')
        finally:
            with self._goal_handle_lock:
                self._active_goal_handle = None
