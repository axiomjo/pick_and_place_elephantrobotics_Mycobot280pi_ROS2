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
        # Convert to ROS messages (e.g., OneDetectedObject/ManyDetectedObjects/Point2DArray)
        # and send to the planner/action server
        print("Arranged objects:", arranged)
        # ...build and send your action goal her
        
    def update_joint_state(self, joint_state_msg):
        # Display joint angles or update a visualization
        pass

    def send_manual_command(self):
        # Open a dialog or send a test command via ROSCommunication
        self.ros_comm.send_manual_command()

    def open_perspective_editor(self):
        # Open a perspective editor dialog (to be implemented)
        pass


    def closeEvent(self, event):
        self.ros_comm.shutdown()
        event.accept()
