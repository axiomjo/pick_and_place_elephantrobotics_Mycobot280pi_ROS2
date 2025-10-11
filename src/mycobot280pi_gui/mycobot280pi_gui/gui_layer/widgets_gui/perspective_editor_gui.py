"""
perspective_editor_gui.py - Defines the PerspectiveEditorGUI.

This is an interactive widget that displays a camera feed and allows the user
to drag four handles. It emits the coordinates of its handles via a PyQt signal.
"""
import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot

# Import the custom handle item
from .graphics_gui.point_handle_gui import PointHandleGUI

class PerspectiveEditorGUI(QWidget):
    """A widget for interactively selecting four perspective points on an image."""

    perspective_points_changed = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame = None [cite: 259]
        self.handles = [] [cite: 259]
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        
        self.pixmap_item = QGraphicsPixmapItem() [cite: 260]
        self.scene.addItem(self.pixmap_item)
        main_layout.addWidget(self.view)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._emit_points_update)
        self.timer.start(200) # Emit data at 5 Hz

    @pyqtSlot(np.ndarray)
    def update_frame(self, new_frame):
        """Public slot to receive a new camera frame (as a numpy array).""" [cite: 261]
        if new_frame is None or new_frame.size == 0:
            return
        self.frame = new_frame
        
        rgb_image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        h, w, ch = self.frame.shape
        bytes_per_line = ch * w [cite: 264]
        qimg = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item.setPixmap(pixmap)
        
        if not self.handles:
            margin = 50 [cite: 265]
            self.handles = [
                PointHandleGUI(margin, margin),
                PointHandleGUI(w - margin, margin),
                PointHandleGUI(w - margin, h - margin),
                PointHandleGUI(margin, h - margin)
            ] [cite: 265, 266]
            for handle in self.handles:
                self.scene.addItem(handle)

    def _emit_points_update(self):
        """Internal method called by timer to gather and emit handle positions.""" [cite: 267]
        if self.frame is None or not self.handles:
            return
        points = np.array([h.get_point() for h in self.handles], dtype=np.float32)
        self.perspective_points_changed.emit(points) [cite: 268]
