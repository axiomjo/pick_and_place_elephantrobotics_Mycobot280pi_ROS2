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

        # --- Instruction Text ---
        self.instruction_text = QTextEdit(
            "Welcome!\n\nCamera feeds on the left. Draggable working area on the right.\n"
            "Use the 'Import Objects' button to create new objects on the working plane from the detected objects.\n\n"
            "Select an object on the working plane to see its attributes and send its pose to the robot."
        )
        self.instruction_text.setReadOnly(True)
        left_panel.insertWidget(0, self.instruction_text)

        # --- Right Panel: Working Plane, Controls, Detected Objects ---
        right_panel = QVBoxLayout()
        self.working_plane_view = QGraphicsView()
        self.working_plane_scene = QGraphicsScene(self)
        # Set scene rect and center
        self.working_plane_scene.setSceneRect(-300, -300, 600, 600)
        self.working_plane_view.setScene(self.working_plane_scene)
        # Flip y-axis for robot convention
        from PyQt5.QtGui import QTransform
        transform = QTransform()
        transform.scale(1, -1)
        self.working_plane_view.setTransform(transform)
        # Draw working plane cosmetics
        self.draw_mycobot280pi_working_plane()
        self.draw_axes_with_ticks()
        right_panel.addWidget(self.working_plane_view, 2)

        # --- Control buttons for the working plane ---
        controls_h_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset Plane")
        self.reset_btn.clicked.connect(self.reset_plane)
        controls_h_layout.addWidget(self.reset_btn)
        controls_h_layout.addWidget(self.manual_cmd_btn)
        controls_h_layout.addWidget(self.import_objects_btn)
        right_panel.addLayout(controls_h_layout)

        main_layout.addLayout(right_panel, 2)

        # --- Dock Widget for Cutouts and Rotation Controls ---
        self.dock_panel = QDockWidget("Object Cutouts & Controls", self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_panel)
        dock_widget_content = QWidget()
        dock_v_layout = QVBoxLayout(dock_widget_content)
        # Cutout View (placeholder, can be filled in future)
        self.cutout_scene = QGraphicsScene()
        self.cutout_view = QGraphicsView(self.cutout_scene)
        self.cutout_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cutout_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        dock_v_layout.addWidget(QLabel("Detected Object Cutouts:"))
        dock_v_layout.addWidget(self.cutout_view)
        # Rotation Controls
        from PyQt5.QtWidgets import QSlider, QDoubleSpinBox
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)
        self.rotation_spinbox = QDoubleSpinBox()
        self.rotation_spinbox.setRange(-180, 180)
        self.rotation_spinbox.setSingleStep(0.1)
        self.rotation_spinbox.setDecimals(1)
        self.rotation_slider.valueChanged.connect(self.rotation_spinbox.setValue)
        self.rotation_spinbox.valueChanged.connect(self.rotation_slider.setValue)
        self.rotation_spinbox.valueChanged.connect(self.set_selected_item_rotation)
        dock_v_layout.addWidget(QLabel("Rotation (Selected Object):"))
        dock_v_layout.addWidget(self.rotation_slider)
        dock_v_layout.addWidget(self.rotation_spinbox)
        self.rotation_slider.setDisabled(True)
        self.rotation_spinbox.setDisabled(True)
        dock_widget_content.setLayout(dock_v_layout)
        self.dock_panel.setWidget(dock_widget_content)

        # Connect selection change to update rotation controls
        self.working_plane_scene.selectionChanged.connect(self.update_rotation_widgets)

    def reset_plane(self):
        self.working_plane_scene.clear()
        self.draw_mycobot280pi_working_plane()
        self.draw_axes_with_ticks()

    def set_selected_item_rotation(self, angle):
        selected_items = self.working_plane_scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            item.setRotation(angle)

    def update_rotation_widgets(self):
        selected_items = self.working_plane_scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.rotation_slider.setDisabled(False)
            self.rotation_spinbox.setDisabled(False)
            self.rotation_spinbox.setValue(item.rotation())
        else:
            self.rotation_slider.setDisabled(True)
            self.rotation_spinbox.setDisabled(True)

    def draw_axes_with_ticks(self):
        from PyQt5.QtGui import QPen, QColor
        pen_axis = QPen(Qt.black, 2)
        pen_ticks = QPen(Qt.black, 1)
        grid_pen = QPen(QColor(200, 200, 200), 1)
        scene_rect = self.working_plane_scene.sceneRect()
        min_x, max_x = scene_rect.left(), scene_rect.right()
        min_y, max_y = scene_rect.bottom(), scene_rect.top()
        # Draw vertical grid lines
        for x in range(int(min_x), int(max_x) + 1, 5):
            self.working_plane_scene.addLine(x, min_y, x, max_y, grid_pen)
        # Draw horizontal grid lines
        for y in range(int(min_y), int(max_y) + 1, 5):
            self.working_plane_scene.addLine(min_x, y, max_x, y, grid_pen)
        # Draw the main axes
        self.working_plane_scene.addLine(-280, 0, 280, 0, pen_axis)
        self.working_plane_scene.addLine(0, -280, 0, 280, pen_axis)
        # Draw ticks every 50mm
        for x in range(-280, 281, 50):
            if x == 0:
                continue
            length = 12
            self.working_plane_scene.addLine(x, -length / 2, x, length / 2, pen_ticks)
        for y in range(-280, 281, 50):
            if y == 0:
                continue
            length = 12
            self.working_plane_scene.addLine(-length / 2, y, length / 2, y, pen_ticks)

    def draw_mycobot280pi_working_plane(self):
        from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath
        from PyQt5.QtCore import QRectF
        circle_radius = 280.0
        circle_item = self.working_plane_scene.addEllipse(-circle_radius, -circle_radius, 2 * circle_radius, 2 * circle_radius,
                                          pen=QPen(Qt.NoPen), brush=QBrush(QColor(173, 216, 230, 50)))
        circle_item.setZValue(-1)
        rect_width, rect_height, corner_radius = 110, 150, 7.5
        path = QPainterPath()
        path.addRoundedRect(QRectF(-rect_width/2, -rect_height/2, rect_width, rect_height), corner_radius, corner_radius)
        self.working_plane_scene.addPath(path, pen=QPen(Qt.NoPen), brush=QBrush(QColor("#DFDFDF"))).setZValue(0)
        robotbase_radius = 45
        self.working_plane_scene.addEllipse(-robotbase_radius, -robotbase_radius, 2*robotbase_radius, 2*robotbase_radius,
                                       pen=QPen(Qt.NoPen), brush=QBrush(QColor("#C3C3C3"))).setZValue(1)
        face_width, face_height = 20, 60
        face_item = self.working_plane_scene.addRect(-face_width / 2 - 45, -face_height / 2, face_width, face_height)
        face_item.setPen(QPen(Qt.NoPen))
        face_item.setBrush(QBrush(QColor("#C3C3C3")))
        face_item.setZValue(1)
    def periodic_update(self):
        # This method is called periodically by the GUI timer. Add GUI refresh logic if needed.
        pass
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyCobot Robot Control GUI")
        self.resize(1200, 800)

        # --- ROS Communication ---
        self.ros_comm = ROSCommunication(self)
        self.ros_comm.raw_image_received.connect(self.update_raw_camera_feed)
        self.ros_comm.image_received.connect(self.update_camera_feed)
        self.ros_comm.corrected_image_received.connect(self.update_corrected_feed)
        self.ros_comm.detected_objects_received.connect(self.store_detected_objects)
        self.ros_comm.joint_state_received.connect(self.update_joint_state)
        # ...connect other signals as needed...

        # Store the latest detected objects message for import
        self._latest_detected_objects_msg = None

        # --- Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel: Camera Feeds ---
        left_panel = QVBoxLayout()
        self.raw_camera_label = QLabel("Raw Camera Feed")
        self.camera_label = QLabel("Undistorted Feed")
        self.corrected_label = QLabel("Corrected Feed")
        left_panel.addWidget(self.raw_camera_label)
        left_panel.addWidget(self.camera_label)
        left_panel.addWidget(self.corrected_label)
        main_layout.addLayout(left_panel, 1)
   
    def update_raw_camera_feed(self, cv_image):
        rgb_image = cv_image[..., ::-1]
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        self.raw_camera_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.raw_camera_label.width(), self.raw_camera_label.height(), Qt.KeepAspectRatio))

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

    # Import Objects button
    self.import_objects_btn = QPushButton("Import Objects")
    self.import_objects_btn.clicked.connect(self.import_detected_objects)
    right_panel.addWidget(self.import_objects_btn)

    self.plan_execute_btn = QPushButton("MAKE THE SCENE!")
    self.plan_execute_btn.clicked.connect(self.on_send_to_planner_clicked)
    main_layout.addWidget(self.plan_execute_btn)

    # Example: Perspective editor button
    self.perspective_btn = QPushButton("Edit Perspective Points")
    self.perspective_btn.setEnabled(False)  # Disabled until image is available
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
        # Enable perspective button now that we have an image
        self.perspective_btn.setEnabled(True)

    def update_corrected_feed(self, cv_image):
        rgb_image = cv_image[..., ::-1]
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        self.corrected_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.corrected_label.width(), self.corrected_label.height(), Qt.KeepAspectRatio))


    def store_detected_objects(self, objects_msg):
        """Store the latest detected objects message for import."""
        self._latest_detected_objects_msg = objects_msg
        self.detected_objects_label.setText(f"Detected {len(objects_msg.objects)} objects ready to import.")

    def import_detected_objects(self):
        """Spawn draggable items from the last detected objects message when button is clicked."""
        objects_msg = self._latest_detected_objects_msg
        if objects_msg is None or not hasattr(objects_msg, 'objects') or not objects_msg.objects:
            self.status_text.append("[INFO] No detected objects to import.")
            return
        self.working_plane_scene.clear()
        for obj in objects_msg.objects:
            x = obj.center_point.x - obj.width / 2
            y = obj.center_point.y - obj.height / 2
            w = obj.width
            h = obj.height
            item = DraggableObjectItem(x, y, w, h, object_id=obj.id)
            self.working_plane_scene.addItem(item)
        self.detected_objects_label.setText(f"Imported {len(objects_msg.objects)} objects.")
        
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
