
"""
Defines the PerspectiveEditorWidget.

This is an interactive widget that displays a camera feed and allows the user
to drag four handles to define a perspective transformation area.

It is a "dumb" component that has no knowledge of ROS. It receives image frames
via a public slot and emits the coordinates of its handles via a PyQt signal.
"""

import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, pyqtSignal

# Import the custom handle item from its own file
from .grcn_point_handle import PointHandle


class PerspectiveEditorWidget(QWidget):
    """A widget for interactively selecting four perspective points on an image."""

    # Signal that emits the four corner points as a numpy array periodically.
    perspective_points_changed = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)

        # This widget is now fully decoupled from ROS.
        self.frame = None
        self.handles = []
        
        # --- Layout & UI Setup ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        
        # Create an empty item to hold the background image
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        main_layout.addWidget(self.view)
        
        # --- Timer to periodically emit point data ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._emit_points_update)
        self.timer.start(200)  # Emit data at 5 Hz

    def update_frame(self, new_frame: np.ndarray):
        """
        Public slot to receive a new camera frame (as a numpy array).
        This also initializes the draggable handles on the first frame.
        """
        if new_frame is None or new_frame.size == 0:
            return
            
        self.frame = new_frame
        
        # Convert the OpenCV image (BGR) to a QPixmap (RGB)
        rgb_image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        h, w, ch = self.frame.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item.setPixmap(pixmap)
        
        # Initialize handles only once, after the first frame has set the size
        if not self.handles:
            # Place handles at the corners with some margin
            margin = 50
            self.handles = [
                PointHandle(margin, margin),
                PointHandle(w - margin, margin),
                PointHandle(w - margin, h - margin),
                PointHandle(margin, h - margin)
            ]
            for handle in self.handles:
                self.scene.addItem(handle)

    def _emit_points_update(self):
        """
        Internal method called by the timer. It gathers handle positions
        and emits them via a signal.
        """
        if self.frame is None or not self.handles:
            return

        # Get the current (x, y) position of each handle
        points = np.array([h.get_point() for h in self.handles], dtype=np.float32)

        # Emit the signal with the points data
        self.perspective_points_changed.emit(points)
