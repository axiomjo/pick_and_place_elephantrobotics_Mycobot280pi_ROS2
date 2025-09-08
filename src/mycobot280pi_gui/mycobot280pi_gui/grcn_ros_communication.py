"""
grcn_ros_communication.py

Handles all ROS2 communication for the GUI node.
Subscribes to camera feeds, detected objects, and joint states.
Publishes manual commands and perspective points.
Provides service and action clients for planner interaction.
Emits PyQt signals to update the GUI.
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from sensor_msgs.msg import Image, JointState
from mycobot280pi_interfaces.msg import ManyDetectedObjects, SimpleCommands, Point2DArray
from mycobot280pi_interfaces.srv import Mycobot280PiSetCoordsMadeSure
from mycobot280pi_interfaces.action import ProcessWorkspace

from cv_bridge import CvBridge
import numpy as np

class ROSCommunication(QObject):
    # PyQt signals for GUI updates
    image_received = pyqtSignal(np.ndarray)
    corrected_image_received = pyqtSignal(np.ndarray)
    detected_objects_received = pyqtSignal(ManyDetectedObjects)
    joint_state_received = pyqtSignal(JointState)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bridge = CvBridge()
        self._ros_thread = QThread()
        self._ros_node = _ROSNode(self)
        self._ros_node.moveToThread(self._ros_thread)
        self._ros_thread.started.connect(self._ros_node.run)
        self._ros_thread.start()

    def send_manual_command(self, command_type="move", coords=None, speed=50):
        # Example: send a manual command to the planner
        cmd = SimpleCommands()
        cmd.command_type = command_type
        if coords:
            cmd.coords = coords
        cmd.speed = speed
        self._ros_node.publish_manual_command(cmd)

    def send_perspective_points(self, points):
        # points: list of (x, y)
        msg = Point2DArray()
        for x, y in points:
            pt = msg.points.add()
            pt.x = float(x)
            pt.y = float(y)
        self._ros_node.publish_perspective_points(msg)

    def call_set_coords_service(self, coords, speed, callback):
        self._ros_node.call_set_coords_service(coords, speed, callback)

    def send_process_workspace_goal(self, objects_to_move, target_positions, target_orientation, feedback_cb, result_cb):
        self._ros_node.send_process_workspace_goal(objects_to_move, target_positions, target_orientation, feedback_cb, result_cb)

    def shutdown(self):
        self._ros_node.shutdown()
        self._ros_thread.quit()
        self._ros_thread.wait()

class _ROSNode(Node):
    def __init__(self, gui_comm):
        super().__init__('gui_robot_control_node')
        self.gui_comm = gui_comm
        self.bridge = CvBridge()

        # Subscribers
        self.create_subscription(Image, '/vision/undistorted_image', self.image_cb, 10)
        self.create_subscription(Image, '/vision/corrected_image', self.corrected_image_cb, 10)
        self.create_subscription(ManyDetectedObjects, '/vision/detected_objects', self.detected_objects_cb, 10)
        self.create_subscription(JointState, '/robot/joint_states', self.joint_state_cb, 10)

        # Publishers
        self.manual_cmd_pub = self.create_publisher(SimpleCommands, '/planner/manual_commands', 10)
        self.perspective_points_pub = self.create_publisher(Point2DArray, '/vision/perspective_points', 10)

        # Service client
        self.set_coords_cli = self.create_client(Mycobot280PiSetCoordsMadeSure, '/planner/set_coords')

        # Action client
        from rclpy.action import ActionClient
        self.process_workspace_ac = ActionClient(self, ProcessWorkspace, '/planner/process_workspace')

        self.executor = SingleThreadedExecutor()
        self.executor.add_node(self)

    def run(self):
        rclpy.spin(self, executor=self.executor)

    # --- Subscriber Callbacks ---
    def image_cb(self, msg):
        cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.gui_comm.image_received.emit(cv_img)

    def corrected_image_cb(self, msg):
        cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.gui_comm.corrected_image_received.emit(cv_img)

    def detected_objects_cb(self, msg):
        self.gui_comm.detected_objects_received.emit(msg)

    def joint_state_cb(self, msg):
        self.gui_comm.joint_state_received.emit(msg)

    # --- Publishers ---
    def publish_manual_command(self, cmd):
        self.manual_cmd_pub.publish(cmd)

    def publish_perspective_points(self, msg):
        self.perspective_points_pub.publish(msg)

    # --- Service Client ---
    def call_set_coords_service(self, coords, speed, callback):
        req = Mycobot280PiSetCoordsMadeSure.Request()
        req.coords = coords
        req.speed = speed
        future = self.set_coords_cli.call_async(req)
        future.add_done_callback(lambda fut: callback(fut.result()))

    # --- Action Client ---
    def send_process_workspace_goal(self, objects_to_move, target_positions, target_orientation, feedback_cb, result_cb):
        from mycobot280pi_interfaces.action import ProcessWorkspace
        goal_msg = ProcessWorkspace.Goal()
        goal_msg.objects_to_move = objects_to_move
        goal_msg.objects_target_position = target_positions
        goal_msg.objects_target_orientation = target_orientation

        send_goal_future = self.process_workspace_ac.send_goal_async(
            goal_msg,
            feedback_callback=lambda feedback: feedback_cb(feedback.feedback)
        )
        def _result_callback(fut):
            result = fut.result().result
            result_cb(result)
        send_goal_future.add_done_callback(
            lambda fut: fut.result().get_result_async().add_done_callback(_result_callback)
        )

    def shutdown(self):
        self.destroy_node()
