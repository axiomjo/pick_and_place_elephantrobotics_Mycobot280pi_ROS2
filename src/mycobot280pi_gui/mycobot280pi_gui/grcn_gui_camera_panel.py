"""
docstring plz
"""
# grcn_gui_camera_panel.py


import cv2
from cv_bridge import CvBridge

import numpy as np

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QTextEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, Qt

from mycobot280pi_interfaces.msg import Point2DArray, Point2D

#from other grcn files
from .grcn_pyqt_widget import PointHandle


class PerspectiveEditorWidget(QWidget):
    def __init__(self, node, parent=None):
        super().__init__(parent)

        self.node = node
        self.bridge = CvBridge()
        self.frame = None
        self.handles = []
        
        # ----- Layout
        main_layout = QVBoxLayout(self) # Apply layout directly to this widget
        
        # ----- Top: graphics scene
        self.perspectivepoints_scene = QGraphicsScene()
        self.view = QGraphicsView(self.perspectivepoints_scene)
        self.pixmap_item = QGraphicsPixmapItem() # Create an empty item to hold the image
        self.perspectivepoints_scene.addItem(self.pixmap_item)
        main_layout.addWidget(self.view)
        
        # ----- Right side: warped preview + button
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_preview_and_publish)
        self.timer.start(200)  # 5 Hz

    def update_frame(self, new_frame):
        """Public method for MainWindow to send new frames to this widget."""
        if new_frame is None:
            return
        self.frame = new_frame
        
        rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        h, w, ch = self.frame.shape
        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item.setPixmap(pixmap)
        
        # Initialize handles only once
        if not self.handles:
            self.handles = [
                PointHandle(50, 50),
                PointHandle(w-50, 50),
                PointHandle(w-50, h-50),
                PointHandle(50, h-50)
            ]
            for hnd in self.handles:
                self.perspectivepoints_scene.addItem(hnd)

    def update_preview_and_publish(self):
        if self.frame is None or not self.handles:
            return

        pts = np.array([h.get_point() for h in self.handles], dtype=np.float32)

        # Publish Point2DArray
        msg = Point2DArray()
        for (x, y) in pts:
            pt = Point2D()
            pt.x, pt.y = float(x), float(y)
            msg.points.append(pt)
         
        self.node.publish_four_points(pts)
        

class CameraPanel(QWidget):
    def __init__(self, ros_node, parent=None):
        super().__init__(parent)
        self.ros_node = ros_node
        self.initUI()
        self.connect_signals()
        
        
    def initUI(self):
        layout = QVBoxLayout(self)

        # Annotated camera view
        self.camera_label = QLabel("Waiting for annotated camera feed...")
        self.camera_label.setFixedSize(200, 200)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("border: 1px solid black;")
        layout.addWidget(self.camera_label)

        # Embedded perspective editor
        self.perspective_editor = PerspectiveEditorWidget(node=self.ros_node, parent=self)
        layout.addWidget(self.perspective_editor)

        # Joint states display
        self.joint_states_label = QTextEdit("Waiting for joint states...")
        self.joint_states_label.setReadOnly(True)
        self.joint_states_label.setMaximumHeight(150)
        layout.addWidget(self.joint_states_label)    
        
    def connect_signals(self):
        self.ros_node.annotated_image_received.connect(self.update_camera_view)
        self.ros_node.undistorted_image_received.connect(self.perspective_editor.update_frame)
        self.ros_node.joint_state_received.connect(self.update_joint_display)
        
    def update_camera_view(self, cv_image):
        """Displays the annotated image."""
        # 1. Convert colors: OpenCV uses Blue-Green-Red (BGR), but Qt needs Red-Green-Blue (RGB).
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        
        # 2. Convert format: Create a QImage from the raw image data.
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        
        # 3. Create a QPixmap (a displayable image) and scale it to fit the label.
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(200,200, Qt.KeepAspectRatio)
        
        # 4. "Plop" the final image onto the label widget.
        self.camera_label.setPixmap(scaled_pixmap)

    def update_joint_display(self, joint_state_msg):
        """Displays the latest joint states."""
        text = "Joint States:\n"
        for i, name in enumerate(joint_state_msg.name):
            angle_deg = np.rad2deg(joint_state_msg.position[i])
            text += f"- {name}: {angle_deg:.2f}°\n"
        self.joint_states_label.setText(text)
        
        
        
        
