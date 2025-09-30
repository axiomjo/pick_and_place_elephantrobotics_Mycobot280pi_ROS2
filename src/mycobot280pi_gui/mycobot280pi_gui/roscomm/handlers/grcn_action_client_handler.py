
"""
Defines the ActionClientHandler class.

This class encapsulates all logic for interacting with a specific ROS 2 Action Client.
It follows the Single Responsibility Principle, where its only job is to manage
the lifecycle of an action: sending goals, processing feedback, handling results,
and managing cancellations.

It is created by the ROSOrchestratorNode and is provided with a node instance
and a facade reference.
"""

import rclpy.node
from PyQt5.QtCore import QObject
from rclpy.action import ActionClient
import threading

# Import the specific action and its related messages
from mycobot280pi_interfaces.action import ProcessWorkspace
from action_msgs.msg import GoalStatus

ACTION_COMPLEX_COMMAND = '/planner/act_complex_command'


class ActionClientHandler:
    """Manages all interactions with the ProcessWorkspace action client."""

    def __init__(self, node: rclpy.node.Node, facade: QObject):
        """
        Initializes the action client handler.
        
        Args:
            node: The ROSOrchestratorNode instance to create the client on.
            facade: The ROSCommunication facade instance to emit signals.
        """
        self._node = node
        self._facade = facade
        
        self._action_client = ActionClient(
            node=self._node,
            action_type=ProcessWorkspace,
            action_name=ACTION_COMPLEX_COMMAND
        )
        
        # A lock is crucial to prevent race conditions when accessing the goal handle
        # from different callbacks or threads.
        self._goal_handle_lock = threading.Lock()
        self._active_goal_handle = None

    def send_goal(self, objects_to_move, target_positions, target_orientation):
        """Constructs and sends a goal to the action server."""
        if not self._action_client.wait_for_server(timeout_sec=2.0):
            self._node.get_logger().error('Action server not available!')
            self._facade.action_result.emit(False, 'Action server not available')
            return
            
        goal_msg = ProcessWorkspace.Goal()
        goal_msg.objects_to_move = objects_to_move
        goal_msg.objects_target_position = target_positions
        goal_msg.objects_target_orientation = target_orientation
        
        self._node.get_logger().info('Sending complex action goal...')
        
        # Send the goal asynchronously and add callbacks to handle the response
        send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback
        )
        send_goal_future.add_done_callback(self._goal_response_callback)

    def cancel_goal(self):
        """Sends a cancellation request for the currently active goal."""
        with self._goal_handle_lock:
            if self._active_goal_handle is None:
                self._node.get_logger().warn('No active goal to cancel.')
                return

            # Check the status against the GoalStatus enum
            status = self._active_goal_handle.status
            if status == GoalStatus.STATUS_ACCEPTED or status == GoalStatus.STATUS_EXECUTING:
                self._node.get_logger().info('Cancelling the active goal...')
                cancel_future = self._active_goal_handle.cancel_goal_async()
                cancel_future.add_done_callback(self._cancel_done_callback)
            else:
                self._node.get_logger().warn(f"Goal is not in an active state (current status: {status}), cannot cancel.")
       
    # --- Private Action Callbacks ---

    def _goal_response_callback(self, future):
        """Handles the server's response to the goal submission."""
        goal_handle = future.result() 
        if not goal_handle.accepted:
            self._node.get_logger().info('Goal was rejected by the server.')
            self._facade.action_result.emit(False, 'Goal rejected')
            return

        self._node.get_logger().info('Goal was accepted by the server.')
        
        with self._goal_handle_lock:
            self._active_goal_handle = goal_handle
        
        # Request the final result of the action
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _feedback_callback(self, feedback_msg):
        """Receives and processes feedback messages during action execution."""
        feedback = feedback_msg.feedback.current_state
        self._facade.action_feedback.emit(feedback)

    def _result_callback(self, future):
        """Receives and processes the final result of the action."""
        try:
            result = future.result().result
            self._node.get_logger().info(f'Action finished with result: {result.message}')
            self._facade.action_result.emit(result.success, result.message)
        except Exception as e:
            self._node.get_logger().error(f'Exception while getting action result: {e}')
            self._facade.action_result.emit(False, f'Exception: {e}')
        finally:
            # Clear the active goal handle once the action is done
            with self._goal_handle_lock:
                self._active_goal_handle = None
   
    def _cancel_done_callback(self, future):
        """Logs the result of the cancellation request."""
        cancel_response = future.result()
        if len(cancel_response.goals_canceling) > 0:
            self._node.get_logger().info('Goal cancellation request was successful.')
        else:
            self._node.get_logger().warn('Goal cancellation failed (goal may have already finished).')
