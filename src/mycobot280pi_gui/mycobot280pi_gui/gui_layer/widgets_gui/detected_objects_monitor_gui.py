"""
detected_objects_monitor_gui.py - Defines the DetectedObjectMonitorGUI.

This View's sole responsibility is to display an image (the annotated camera feed)
that it receives via its public update_camera_view slot.
"""
import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSlot

class DetectedObjectMonitorGUI(QWidget):
    """A widget that displays the annotated camera feed."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.camera_label = QLabel("Waiting for annotated camera feed...") 
        self.camera_label.setFixedSize(300, 300) 
        self.camera_label.setAlignment(Qt.AlignCenter) 
        self.camera_label.setStyleSheet("border: 1px solid black; background-color: #222;") 
        layout.addWidget(self.camera_label)

    @pyqtSlot(np.ndarray)
    def update_camera_view(self, cv_image):
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
            
            self.camera_label.setPixmap(pixmap.scaled(
                self.camera_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )) 
        except Exception as e:
            self.camera_label.setText("Error displaying image.")
            print(f"Error in update_camera_view: {e}") 
