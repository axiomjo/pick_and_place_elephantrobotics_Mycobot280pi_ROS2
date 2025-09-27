"""
Todo: cakepin format createsubscription dll supaya g sebaris
ganti nama pyqt signalnya

apus/ gabungin yg bagus dari file lawas di bawah ke atas
"""

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



"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
import threading
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal
from cv_bridge import CvBridge

# ROS2 interfaces
from sensor_msgs.msg import Image, JointState
from mycobot280pi_interfaces.msg import Point2D, Point2DArray, ManyDetectedObjects
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure
from mycobot280pi_interfaces.action import ProcessWorkspace


# --- Constants (single source of truth for interface names) ---
TOPIC_UNDISTORTED_IMAGE = '/vision/msg_undistorted_image'
TOPIC_DETECTED_OBJECTS = '/vision/msg_detected_objects'
TOPIC_ANNOTATED_IMAGE = '/vision/msg_annotated_image'
TOPIC_JOINT_ANGLES = '/robot/msg_joint_angles'
TOPIC_FOUR_POINTS = '/gui/msg_four_perspective_points'

SERVICE_SIMPLE_COMMAND = '/planner/srv_simple_command'
ACTION_COMPLEX_COMMAND = '/planner/act_complex_command'



# =========================================================================
#  Part 1: The Manager Class (ROSCommunication)
# =========================================================================
class ROSCommunication(QObject):
    """
    This is the Head Chef (Manager). The GUI talks to this class.
    It provides simple methods and forwards the hard work to the Line Cook (_ROSNode).
    """
    # These are the "notification bells". The Head Chef rings these to alert
    # the Waiters (GUI) that something is ready (e.g., a new image has arrived).
    undistorted_image_received = pyqtSignal(np.ndarray)
    annotated_image_received = pyqtSignal(np.ndarray)
    detected_objects_received = pyqtSignal(ManyDetectedObjects)
    joint_state_received = pyqtSignal(JointState)
    simple_command_response = pyqtSignal(bool, str)
    action_feedback = pyqtSignal(str)
    action_result = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        """
        This runs when the restaurant opens for the day.
        """
        super().__init__(parent)
        
        # 1. The Head Chef hires their expert Line Cook (_ROSNode).
        self._ros_node = _ROSNode(self)
        
        # 2. The Head Chef opens the Kitchen (a new thread), and tells the
        #    Line Cook to start working there continuously.
        self.executor = MultiThreadedExecutor()
        self.executor.add_node(self._ros_node)
        self.ros_thread = threading.Thread(target=self.executor.spin)
        self.ros_thread.daemon = True  # Allows the ros node to close when gui is closed
        self.ros_thread.start()
        print("GUI's node is ready!")

    # --- Public Methods for the GUI ---
    # These are the simple orders the Waiters (GUI) give to the Head Chef.
    # The Head Chef just passes the order to the Line Cook.
    
    def publish_four_points(self, points):
        """Waiter says: 'Chef, here are the four corner points from the customer.'"""
        self._ros_node.publish_perspective_points(points)

    def call_simple_command(self, coords=None, speed=50, is_linear_mode=True):
        """Waiter says: 'Chef, the customer wants a simple robot move.'"""
        self._ros_node.call_simple_command_service(coords or [], speed, is_linear_mode)

    def send_complex_goal(self, objects_to_move, target_positions, target_orientation):
        """Waiter says: 'Chef, the customer wants a complex pick-and-place order.'"""
        self._ros_node.send_complex_action_goal(objects_to_move, target_positions, target_orientation)

    def cancel_complex_goal(self):
        """Waiter says: 'Chef, cancel that complex order!'"""
        self._ros_node.cancel_complex_goal()

    def shutdown(self):
        """This is the 'closing time' procedure to safely shut down the kitchen."""
        print("Closing the kitchen...")
        self.executor.shutdown()
        self._ros_node.destroy_node()
        
        
        
        
        
class _ROSNode(Node):
    """
    Internal rclpy Node that lives entirely inside the background thread.
    (Reorganized for clarity)
    """
    def __init__(self, facade: ROSCommunication):
        super().__init__('gui_robot_control_node')
        self.facade = facade
        self.bridge = CvBridge()
        self._active_action_goal = None

        # --- Group 1: Publishers & Clients (Setup) ---
        # All outgoing communication channels are set up here.
        self.points_pub = self.create_publisher(Point2DArray, TOPIC_FOUR_POINTS, 10)
        self.simple_cmd_client = self.create_client(Mycobot280PiSimpleCommandsMadeSure, SERVICE_SIMPLE_COMMAND)
        self.action_client = ActionClient(self, ProcessWorkspace, ACTION_COMPLEX_COMMAND)

        # --- Group 2: Subscribers (Setup) ---
        # All incoming communication channels are set up here.
        self.create_subscription(Image, TOPIC_UNDISTORTED_IMAGE, self._undistorted_cb, 10)
        self.create_subscription(Image, TOPIC_ANNOTATED_IMAGE, self._annotated_cb, 10)
        self.create_subscription(ManyDetectedObjects, TOPIC_DETECTED_OBJECTS, self._objects_cb, 10)
        self.create_subscription(JointState, TOPIC_JOINT_ANGLES, self._joints_cb, 10)

    # =========================================================================
    #  Methods for INCOMING Data (Subscriber Callbacks)
    # =========================================================================
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

    # =========================================================================
    #  Methods for OUTGOING Data (Publisher)
    # =========================================================================
    def publish_perspective_points(self, points):
        msg = Point2DArray()
        for x, y in points:
            pt = Point2D()
            pt.x, pt.y = float(x), float(y)
            msg.points.append(pt)
        self.points_pub.publish(msg)

    # =========================================================================
    #  Methods for Quick Tasks (Service Client)
    # =========================================================================
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

    # =========================================================================
    #  Methods for Complex, Multi-Step Tasks (Action Client)
    # =========================================================================
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
            
    # =========================================================================
    #  Shutdown Method
    # =========================================================================
    def shutdown(self):
        try:
            self.destroy_node()
        except Exception:
            pass



























