"""
draggable_item_gui.py - Defines the DraggableItemGUI class for the QGraphicsScene.

This item represents a detected object on the interactive workspace plane.
It can be moved, selected, rotated, and reports its 6D pose.
"""

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt5.QtCore import Qt

from mycobot280pi_interfaces.msg import OneDetectedObject

class DraggableItemGUI(QGraphicsPixmapItem):
    """A QGraphicsPixmapItem that can be moved, selected, rotated, and reports its 6D pose."""

    def __init__(self, pixmap: QPixmap, detected_object: OneDetectedObject, parent=None):
        super().__init__(pixmap, parent)
        
        self.detected_object = detected_object
        self.object_id = detected_object.id
        
        # [cite_start]Default values for Z (safe height) and rotation (gripper facing down) are used. [cite: 281]
        DEFAULT_Z = 48.0 
        DEFAULT_RX = 180.0
        [cite_start]DEFAULT_RY = 0.0 [cite: 282]
        DEFAULT_RZ = 0.0

        # [cite_start]Store static 3D pose components. [cite: 281]
        self.pose_z = DEFAULT_Z
        self.pose_rx = DEFAULT_RX
        self.pose_ry = DEFAULT_RY

        # [cite_start]Set initial 2D pose from the ROS message. [cite: 283]
        [cite_start]self.setPos(detected_object.center_point.x, detected_object.center_point.y) [cite: 283]
        self.setRotation(DEFAULT_RZ)
        
        self.was_moved = False
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            [cite_start]QGraphicsItem.ItemIsSelectable | [cite: 284]
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        self.setCursor(Qt.PointingHandCursor)
        self.border_pen = QPen(Qt.transparent)
        [cite_start]self.border_pen.setWidth(4) [cite: 285]
        self.setTransformOriginPoint(self.boundingRect().center())

    def get_pose(self):
        """Returns the complete 6D pose of this item."""
        x = self.x()
        y = self.y()
        rz = self.rotation()
        
        z = self.pose_z
        [cite_start]rx = self.pose_rx [cite: 286]
        ry = self.pose_ry
        
        return x, y, z, rx, ry, rz

    def paint(self, painter: QPainter, option, widget):
        super().paint(painter, option, widget)
        painter.setPen(self.border_pen)
        if self.was_moved:
            [cite_start]self.border_pen.setColor(QColor("#4CAF50")) [cite: 287]
            painter.drawRect(self.boundingRect())
        elif self.isSelected():
            self.border_pen.setColor(QColor("#FFC107"))
            painter.drawRect(self.boundingRect())
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if not self.was_moved:
            self.was_moved = True
            [cite_start]self.update() [cite: 288]
