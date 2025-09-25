"""grcn_ros_communication.py

Central ROS2 communication layer for the gui_robot_control_node.

Implements ALL external interfaces described in the architecture spec:

Subscribers
-----------
1. /vision/msg_undistorted_image -> sensor_msgs/msg/Image (for perspective editing)
2. /vision/msg_detected_objects  -> mycobot280pi_interfaces/msg/ManyDetectedObjects
3. /vision/msg_annotated_image   -> sensor_msgs/msg/Image (annotated top-down / workspace)
4. /robot/msg_joint_angles       -> sensor_msgs/msg/JointState

Publisher
---------
1. /gui/msg_four_perspective_points -> mycobot280pi_interfaces/msg/Point2DArray

Service Client
--------------
1. /planner/srv_simple_command -> mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure

Action Client
-------------
1. /planner/act_complex_command -> mycobot280pi_interfaces/action/ProcessWorkspace

Design Notes
------------
* Runs rclpy spin inside a QThread so the PyQt GUI thread remains responsive.
* Emits PyQt signals carrying decoded numpy arrays or message objects.
* Provides thin wrapper methods that higher level GUI widgets can call.
* Topic / service / action names are centralized as constants for easy future refactor.
"""

import rclpy
from rclpy.node import Node
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from sensor_msgs.msg import Image, JointState
from mycobot280pi_interfaces.msg import (ManyDetectedObjects, SimpleCommands,
                                         Point2DArray, Point2D)
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure
from mycobot280pi_interfaces.action import ProcessWorkspace

from cv_bridge import CvBridge
import numpy as np
import rclpy
from rclpy.action import ActionClient

# ---------------------------------------------------------------------------
# Constants (single source of truth for interface names)
# ---------------------------------------------------------------------------
TOPIC_UNDISTORTED_IMAGE = '/vision/msg_undistorted_image'
TOPIC_DETECTED_OBJECTS = '/vision/msg_detected_objects'
TOPIC_ANNOTATED_IMAGE = '/vision/msg_annotated_image'
TOPIC_JOINT_ANGLES = '/robot/msg_joint_angles'
TOPIC_FOUR_POINTS = '/gui/msg_four_perspective_points'

SERVICE_SIMPLE_COMMAND = '/planner/srv_simple_command'
ACTION_COMPLEX_COMMAND = '/planner/act_complex_command'

class ROSCommunication(QObject):
    """Facade object exposed to GUI widgets (lives in the GUI thread)."""

    # --- PyQt Signals ---
    undistorted_image_received = pyqtSignal(np.ndarray)   # Perspective editing
    annotated_image_received = pyqtSignal(np.ndarray)     # Workspace / annotated view
    detected_objects_received = pyqtSignal(ManyDetectedObjects)
    joint_state_received = pyqtSignal(JointState)
    simple_command_response = pyqtSignal(bool, str)       # success, message
    action_feedback = pyqtSignal(str)                     # current_state
    action_result = pyqtSignal(bool, str)                 # success, message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bridge = CvBridge()
        self._ros_thread = QThread()
        self._ros_node = _ROSNode(self)
        self._ros_thread.started.connect(self._ros_node.spin)
        self._ros_thread.start()

    # ------------------------------------------------------------------
    # Outgoing interface methods (called by GUI widgets)
    # ------------------------------------------------------------------
    def publish_four_points(self, points):
        """Publish user selected perspective rectangle.
        points: list[(x, y)] length==4
        """
        msg = Point2DArray()
        for x, y in points:
            pt = Point2D()
            pt.x = float(x)
            pt.y = float(y)
            msg.points.append(pt)
        self._ros_node.publish_perspective_points(msg)

    def call_simple_command(self, coords=None, speed=50, is_linear_mode=True):
        self._ros_node.call_simple_command_service(coords or [], speed, is_linear_mode)

    def send_complex_goal(self, objects_to_move, target_positions, target_orientation):
        self._ros_node.send_complex_action_goal(objects_to_move, target_positions, target_orientation)

    def cancel_complex_goal(self):
        self._ros_node.cancel_action_goal()

    def shutdown(self):
        self._ros_node.shutdown()
        self._ros_thread.quit()
        self._ros_thread.wait()


class _ROSNode(Node):
    """Internal rclpy Node that lives entirely inside a QThread."""
    def __init__(self, facade: ROSCommunication):  # type: ignore[name-defined]
        super().__init__('gui_robot_control_node')
        self.facade = facade
        self.bridge = CvBridge()

        # Publishers & Clients (created early for simplicity)
        self.points_pub = self.create_publisher(Point2DArray, TOPIC_FOUR_POINTS, 10)
        self.simple_cmd_client = self.create_client(Mycobot280PiSimpleCommandsMadeSure, SERVICE_SIMPLE_COMMAND)
        self.action_client = ActionClient(self, ProcessWorkspace, ACTION_COMPLEX_COMMAND)
        self._active_action_goal = None

        # Subscribers
        self.create_subscription(Image, TOPIC_UNDISTORTED_IMAGE, self._undistorted_cb, 10)
        self.create_subscription(Image, TOPIC_ANNOTATED_IMAGE, self._annotated_cb, 10)
        self.create_subscription(ManyDetectedObjects, TOPIC_DETECTED_OBJECTS, self._objects_cb, 10)
        self.create_subscription(JointState, TOPIC_JOINT_ANGLES, self._joints_cb, 10)

    # ----------------- Spin Loop -----------------
    def spin(self):
        rclpy.spin(self)

    # ----------------- Subscriber Callbacks -----------------
    def _undistorted_cb(self, msg: Image):
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.facade.undistorted_image_received.emit(cv_img)
        except Exception as e:
            self.get_logger().warn(f"Failed undistorted image conversion: {e}")

    def _annotated_cb(self, msg: Image):
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.facade.annotated_image_received.emit(cv_img)
        except Exception as e:
            self.get_logger().warn(f"Failed annotated image conversion: {e}")

    def _objects_cb(self, msg: ManyDetectedObjects):
        self.facade.detected_objects_received.emit(msg)

    def _joints_cb(self, msg: JointState):
        self.facade.joint_state_received.emit(msg)

    # ----------------- Publishers -----------------
    def publish_perspective_points(self, msg: Point2DArray):
        self.points_pub.publish(msg)

    # ----------------- Service Call -----------------
    def call_simple_command_service(self, coords, speed, is_linear_mode):
        if not self.simple_cmd_client.wait_for_service(timeout_sec=1.0):
            self.facade.simple_command_response.emit(False, 'Service unavailable')
            return
        req = Mycobot280PiSimpleCommandsMadeSure.Request()
        req.coords = list(map(float, coords))
        req.speed = int(speed)
        req.is_linear_mode = bool(is_linear_mode)
        future = self.simple_cmd_client.call_async(req)
        future.add_done_callback(self._simple_command_done)

    def _simple_command_done(self, fut):
        try:
            resp = fut.result()
            self.facade.simple_command_response.emit(resp.success, resp.message)
        except Exception as e:
            self.facade.simple_command_response.emit(False, f'Exception: {e}')

    # ----------------- Action Goal -----------------
    def send_complex_action_goal(self, objects_to_move, target_positions, target_orientation):
        if not self.action_client.wait_for_server(timeout_sec=1.0):
            self.facade.action_result.emit(False, 'Action server not available')
            return
        goal_msg = ProcessWorkspace.Goal()
        goal_msg.objects_to_move = objects_to_move
        goal_msg.objects_target_position = target_positions
        goal_msg.objects_target_orientation = target_orientation
        send_future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self._action_feedback
        )
        send_future.add_done_callback(self._goal_response)

    def _goal_response(self, fut):
        goal_handle = fut.result()
        if not goal_handle.accepted:
            self.facade.action_result.emit(False, 'Goal rejected')
            return
        self._active_action_goal = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._action_result)

    def _action_feedback(self, feedback_msg):
        try:
            self.facade.action_feedback.emit(feedback_msg.feedback.current_state)
        except Exception:
            pass

    def _action_result(self, fut):
        try:
            result = fut.result().result
            self.facade.action_result.emit(result.success, result.message)
        except Exception as e:
            self.facade.action_result.emit(False, f'Exception: {e}')
        self._active_action_goal = None

    def cancel_action_goal(self):
        if self._active_action_goal:
            cancel_future = self._active_action_goal.cancel_goal_async()
            cancel_future.add_done_callback(lambda _: self.facade.action_result.emit(False, 'Cancelled'))
        else:
            self.facade.action_result.emit(False, 'No active goal to cancel')

    # ----------------- Shutdown -----------------
    def shutdown(self):
        try:
            self.destroy_node()
        except Exception:
            pass
