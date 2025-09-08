"""
grcn_pyqt_gui_app.py

Main PyQt5 GUI window for gui_robot_control_node.
Displays camera feeds, detected objects, robot state, and provides controls for manual and automated operation.
"""

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsView, QGraphicsScene, QTextEdit, QDockWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage

from .grcn_ros_communication import ROSCommunication  # Your ROS2 communication class
from .grcn_pyqt_widget import DraggableObjectItem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyCobot Robot Control GUI")
        self.resize(1200, 800)

        # --- ROS Communication ---
        self.ros_comm = ROSCommunication(self)
        self.ros_comm.image_received.connect(self.update_camera_feed)
        self.ros_comm.corrected_image_received.connect(self.update_corrected_feed)
        self.ros_comm.detected_objects_received.connect(self.update_detected_objects)
        self.ros_comm.joint_state_received.connect(self.update_joint_state)
        # ...connect other signals as needed...

        # --- Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel: Camera Feed ---
        left_panel = QVBoxLayout()
        self.camera_label = QLabel("Camera Feed")
        self.corrected_label = QLabel("Corrected Feed")
        left_panel.addWidget(self.camera_label)
        left_panel.addWidget(self.corrected_label)
        main_layout.addLayout(left_panel, 1)

        # --- Right Panel: Working Plane, Controls, Detected Objects ---
        right_panel = QVBoxLayout()
        self.working_plane_view = QGraphicsView()
        self.working_plane_scene = QGraphicsScene(self)
        self.working_plane_view.setScene(self.working_plane_scene)
        right_panel.addWidget(self.working_plane_view, 2)

        # --- Detected Objects Dock ---
        self.dock_panel = QDockWidget("Detected Objects", self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_panel)
        dock_widget_content = QWidget()
        dock_layout = QVBoxLayout(dock_widget_content)
        self.detected_objects_label = QLabel("Detected objects will appear here.")
        dock_layout.addWidget(self.detected_objects_label)
        dock_widget_content.setLayout(dock_layout)
        self.dock_panel.setWidget(dock_widget_content)

        main_layout.addLayout(right_panel, 2)

        # --- Controls (add buttons, sliders, etc. as needed) ---
        # Example: Manual command button
        self.manual_cmd_btn = QPushButton("Send Manual Command")
        self.manual_cmd_btn.clicked.connect(self.send_manual_command)
        right_panel.addWidget(self.manual_cmd_btn)
        
        self.plan_execute_btn = QPushButton("MAKE THE SCENE!")
        self.plan_execute_btn.clicked.connect(self.on_send_to_planner_clicked)
        main_layout.addWidget(self.plan_execute_btn)

        # Example: Perspective editor button
        self.perspective_btn = QPushButton("Edit Perspective Points")
        self.perspective_btn.clicked.connect(self.open_perspective_editor)
        right_panel.addWidget(self.perspective_btn)

        # --- Status/Instruction Text ---
        self.status_text = QTextEdit("Welcome to MyCobot Control GUI!")
        self.status_text.setReadOnly(True)
        right_panel.addWidget(self.status_text)

        # --- Timer for periodic GUI updates (if needed) ---
        self.gui_timer = QTimer(self)
        self.gui_timer.timeout.connect(self.periodic_update)
        self.gui_timer.start(100)  # 10 Hz

    # --- GUI Update Methods (slots for ROS signals) ---
    def collect_arranged_objects(self):
        arranged_objects = []
        for item in self.working_plane_scene.items():
            if isinstance(item, DraggableObjectItem):
                # Get the item's current position in the scene
                pos = item.scenePos()
                obj_dict = {
                    "id": item.object_id,
                    "center_x": pos.x() + item.width / 2,
                    "center_y": pos.y() + item.height / 2,
                    "width": item.width,
                    "height": item.height,
                    # Add more fields if needed (e.g., orientation)
                }
                arranged_objects.append(obj_dict)
        return arranged_objects
        
    def update_camera_feed(self, cv_image):
        # Convert cv2 image to QPixmap and display
        rgb_image = cv_image[..., ::-1]
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.camera_label.width(), self.camera_label.height(), Qt.KeepAspectRatio))
        self._last_undistorted_image = qt_image

    def update_corrected_feed(self, cv_image):
        rgb_image = cv_image[..., ::-1]
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        self.corrected_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.corrected_label.width(), self.corrected_label.height(), Qt.KeepAspectRatio))


    def update_detected_objects(self, objects_msg):
        self.working_plane_scene.clear()
        for obj in objects_msg.objects:
            x = obj.center_point.x - obj.width / 2
            y = obj.center_point.y - obj.height / 2
            w = obj.width
            h = obj.height
            item = DraggableObjectItem(x, y, w, h, object_id=obj.id)
            self.working_plane_scene.addItem(item)
        self.detected_objects_label.setText(f"Detected {len(objects_msg.objects)} objects.")
        
    def on_send_to_planner_clicked(self):
        arranged = self.collect_arranged_objects()
        print("Arranged objects:", arranged)
        # Convert arranged objects to ROS messages
        try:
            from mycobot280pi_interfaces.msg import OneDetectedObject, ManyDetectedObjects, Point2D, Point2DArray
        except ImportError:
            self.status_text.append("[ERROR] ROS message imports failed. Is the interface package built?")
            return

        objects_to_move = []
        target_positions = []
        target_orientations = []

        for obj in arranged:
            # Create OneDetectedObject for each arranged object
            one_obj = OneDetectedObject()
            one_obj.id = str(obj["id"])
            center = Point2D()
            center.x = float(obj["center_x"])
            center.y = float(obj["center_y"])
            one_obj.center_point = center
            one_obj.width = float(obj["width"])
            one_obj.height = float(obj["height"])
            # Optionally set orientation if available
            # one_obj.orientation = ...
            objects_to_move.append(one_obj)
            # For this example, set target positions to current positions (user can edit this logic)
            target_positions.append(center)
            # Optionally set target orientation
            target_orientations.append(0.0)

        # Prepare ManyDetectedObjects message for objects_to_move
        many_objs = ManyDetectedObjects()
        many_objs.objects = objects_to_move

        # Prepare Point2DArray for target positions
        pos_array = Point2DArray()
        pos_array.points = target_positions

        # Prepare orientation list
        orientation_list = target_orientations

        # --- Real-time report: clear status area and show start ---
        self.status_text.clear()
        self.status_text.append("[INFO] Sent arranged objects to planner. Waiting for feedback...")

        def feedback_cb(feedback):
            # Try to extract useful info from feedback (assume feedback has a 'current_step' and 'total_steps' field, adapt as needed)
            msg = "[Planner Feedback] "
            if hasattr(feedback, 'current_step') and hasattr(feedback, 'total_steps'):
                msg += f"Step {feedback.current_step}/{feedback.total_steps}"
            else:
                msg += str(feedback)
            self.status_text.append(msg)

        def result_cb(result):
            # Try to extract useful info from result (assume result has a 'success' and 'message' field, adapt as needed)
            msg = "[Planner Result] "
            if hasattr(result, 'success'):
                msg += f"Success: {result.success}. "
            if hasattr(result, 'message'):
                msg += f"Message: {result.message}"
            else:
                msg += str(result)
            self.status_text.append(msg)

        self.ros_comm.send_process_workspace_goal(
            objects_to_move=objects_to_move,
            target_positions=target_positions,
            target_orientation=orientation_list,
            feedback_cb=feedback_cb,
            result_cb=result_cb
        )
        
    def update_joint_state(self, joint_state_msg):
        # Display joint angles or update a visualization
        pass

    def send_manual_command(self):
        # Open a dialog or send a test command via ROSCommunication
        self.ros_comm.send_manual_command()

    def open_perspective_editor(self):
        # Open a perspective editor dialog for user to select 4 points
        from .grcn_pyqt_widget import PerspectiveEditorDialog
        # Use the latest undistorted image if available
        image = getattr(self, '_last_undistorted_image', None)
        if image is None:
            self.status_text.append("[ERROR] No undistorted image available for perspective editing.")
            return
        dlg = PerspectiveEditorDialog(self, image=image)
        if dlg.exec_() == dlg.Accepted:
            points = dlg.get_points()
            self.ros_comm.send_perspective_points(points)
            self.status_text.append(f"[INFO] Sent perspective points: {points}")
        else:
            self.status_text.append("[INFO] Perspective editing cancelled.")


    def closeEvent(self, event):
        self.ros_comm.shutdown()
        event.accept()
