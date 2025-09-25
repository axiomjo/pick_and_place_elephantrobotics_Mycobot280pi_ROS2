"""grcn_gui_main_window.py

Assembles the full GUI for gui_robot_control_node.
Contains:
- CameraPanel (perspective editing)
- Annotated workspace image (top-down)
- Detected objects dock (placeholder)
- Control panel (buttons / status)

Focus: wiring signals from ROSCommunication to widgets.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDockWidget, QMessageBox, QSizePolicy
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

from .grcn_gui_camera_panel import CameraPanel
from .grcn_ros_communication import ROSCommunication
from .grcn_pyqt_widget import ImageDisplayWidget, PerspectiveEditorDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyCobot 280 Pi Control Center")
        self.resize(1400, 900)

        # --- ROS Communication Layer ---
        self.ros = ROSCommunication()

        # --- Central Widgets ---
        central = QWidget()
        central_layout = QHBoxLayout(central)
        self.setCentralWidget(central)

        # Left: Perspective editing camera panel
        self.camera_panel = CameraPanel(ros_comm=self.ros)
        self.camera_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        central_layout.addWidget(self.camera_panel, 2)

        # Right: Annotated workspace view
        right_container = QVBoxLayout()
        self.annotated_label = ImageDisplayWidget()
        self.annotated_label.setMinimumSize(640, 480)
        right_container.addWidget(self.annotated_label, 3)

        # Control buttons (simplified)
        controls_row = QHBoxLayout()
        self.btn_send_simple = QPushButton("Send Simple Command")
        self.btn_send_simple.clicked.connect(self._on_simple_command)
        self.btn_start_action = QPushButton("Start Complex Action")
        self.btn_start_action.clicked.connect(self._on_start_action)
        self.btn_cancel_action = QPushButton("Cancel Action")
        self.btn_cancel_action.clicked.connect(self._on_cancel_action)
        controls_row.addWidget(self.btn_send_simple)
        controls_row.addWidget(self.btn_start_action)
        controls_row.addWidget(self.btn_cancel_action)
        right_container.addLayout(controls_row)

        # Status labels
        self.status_simple = QLabel("SimpleCmd: idle")
        self.status_action = QLabel("Action: idle")
        right_container.addWidget(self.status_simple)
        right_container.addWidget(self.status_action)

        central_layout.addLayout(right_container, 2)

        # --- Dock: Detected objects placeholder ---
        self.objects_dock = QDockWidget("Detected Objects", self)
        self.objects_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.objects_content = QLabel("(objects will list here)")
        self.objects_content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.objects_dock.setWidget(self.objects_content)
        self.addDockWidget(Qt.RightDockWidgetArea, self.objects_dock)

        # --- Signal Wiring ---
        self.ros.undistorted_image_received.connect(self._update_undistorted_image)
        self.ros.annotated_image_received.connect(self._update_annotated_image)
        self.ros.detected_objects_received.connect(self._update_objects)
        self.ros.joint_state_received.connect(self._update_joint_state)
        self.ros.simple_command_response.connect(self._simple_cmd_response)
        self.ros.action_feedback.connect(self._action_feedback)
        self.ros.action_result.connect(self._action_result)

    # ----------------- GUI Slots -----------------
    def _update_undistorted_image(self, cv_img):
        # Just delegate into camera panel (already subscribed), optional for other overlays
        pass

    def _update_annotated_image(self, cv_img):
        h, w, _ = cv_img.shape
        qimg = QImage(cv_img.data, w, h, 3*w, QImage.Format_RGB888).rgbSwapped()
        self.annotated_label.set_image(qimg)

    def _update_objects(self, msg):
        # Basic textual listing
        lines = [f"{len(msg.objects)} objects"]
        for obj in msg.objects[:10]:  # limit preview
            try:
                oid = getattr(obj, 'id', 'n/a')
                lines.append(f"- id={oid}")
            except Exception:
                lines.append("- <unreadable object>")
        self.objects_content.setText("\n".join(lines))

    def _update_joint_state(self, joint_state):
        # Placeholder: could add a dock with bars later
        pass

    def _simple_cmd_response(self, success, message):
        self.status_simple.setText(f"SimpleCmd: {'OK' if success else 'FAIL'} - {message}")

    def _action_feedback(self, current_state):
        self.status_action.setText(f"Action: {current_state}")

    def _action_result(self, success, message):
        self.status_action.setText(f"Action: {'SUCCESS' if success else 'FAILED'} - {message}")

    # ----------------- Button Handlers -----------------
    def _on_simple_command(self):
        # Example: send a dummy move (empty coords allowed per interface)
        self.status_simple.setText("SimpleCmd: sending...")
        self.ros.call_simple_command(coords=[], speed=40, is_linear_mode=True)

    def _on_start_action(self):
        self.status_action.setText("Action: sending goal...")
        # Placeholder empty goal components (must conform to interface types)
        from mycobot280pi_interfaces.msg import ManyDetectedObjects, Point2DArray
        empty_objects = ManyDetectedObjects()
        target_positions = Point2DArray()
        target_orientation = []  # list[int]
        self.ros.send_complex_goal(empty_objects, target_positions, target_orientation)

    def _on_cancel_action(self):
        self.ros.cancel_complex_goal()

    # ----------------- Lifecycle -----------------
    def closeEvent(self, event):
        try:
            self.ros.shutdown()
        except Exception:
            pass
        event.accept()
