
"""
Defines the CameraPanel, a composite widget for displaying vision-related information.

This panel acts as a container for:
- The main annotated camera feed.
- The interactive perspective editor widget.
- A text display for the robot's joint states.

This widget is designed to be a "dumb" component. It has no knowledge of ROS.
It receives data via public slots that are connected by the MainWindow.
"""

import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QTextEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

# Type hinting for the slot method, does not create a hard dependency on rclpy
from sensor_msgs.msg import JointState

# Import the child widget from the same directory
from .grcn_perspective_editor import PerspectiveEditorWidget


class CameraPanel(QWidget):
    """A widget that groups together various camera and robot state displays."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # This widget no longer accepts a ros_node object.
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Use full space

        # 1. Annotated camera view
        self.camera_label = QLabel("Waiting for annotated camera feed...")
        self.camera_label.setFixedSize(300, 300)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("border: 1px solid black; background-color: #222;")
        layout.addWidget(self.camera_label)

        # 2. Embedded perspective editor
        # The child widget is created without any ROS dependency.
        self.perspective_editor = PerspectiveEditorWidget(parent=self)
        layout.addWidget(self.perspective_editor)

        # 3. Joint states display
        self.joint_states_label = QTextEdit("Waiting for joint states...")
        self.joint_states_label.setReadOnly(True)
        self.joint_states_label.setMaximumHeight(150)
        layout.addWidget(self.joint_states_label)
        
        # The connect_signals() method is removed from here.
        # MainWindow is now responsible for all connections.

    # --- Public Slots ---
    # These methods are designed to be connected to signals from the ROS facade.

    def update_camera_view(self, cv_image: np.ndarray):
        """
        Public slot to display the annotated image from the vision pipeline.
        Converts a cv2 image (numpy array) to a QPixmap.
        """
        try:
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Scale the pixmap to fit the label while maintaining aspect ratio
            self.camera_label.setPixmap(pixmap.scaled(
                self.camera_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        except Exception as e:
            # Handle potential errors without crashing
            print(f"Error in update_camera_view: {e}")
            self.camera_label.setText("Error displaying image.")

    def update_joint_display(self, joint_state_msg: JointState):
        """Public slot to display the latest joint states."""
        text = "<b>Joint States:</b><br>"
        for i, name in enumerate(joint_state_msg.name):
            # Convert radians to degrees for display
            angle_deg = np.rad2deg(joint_state_msg.position[i])
            text += f"&nbsp;&nbsp;- {name}: {angle_deg:.2f}°<br>"
        self.joint_states_label.setHtml(text)
