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
        
        # Default values for Z (safe height) and rotation (gripper facing down) are used.  281]
        DEFAULT_Z = 48.0 
        DEFAULT_RX = 180.0
        DEFAULT_RY = 0.0 
        DEFAULT_RZ = 0.0

        # Store static 3D pose components. 
        self.pose_z = DEFAULT_Z
        self.pose_rx = DEFAULT_RX
        self.pose_ry = DEFAULT_RY

        # Set initial 2D pose from the ROS message. 
        self.setPos(detected_object.center_point.x, detected_object.center_point.y) 
        self.setRotation(DEFAULT_RZ)
        
        self.was_moved = False
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        self.setCursor(Qt.PointingHandCursor)
        self.border_pen = QPen(Qt.transparent)
        self.border_pen.setWidth(4)
        self.setTransformOriginPoint(self.boundingRect().center())

    def get_pose(self):
        """Returns the complete 6D pose of this item."""
        x = self.x()
        y = self.y()
        rz = self.rotation()
        
        z = self.pose_z
        rx = self.pose_rx 
        ry = self.pose_ry
        
        return x, y, z, rx, ry, rz

    def paint(self, painter: QPainter, option, widget):
        super().paint(painter, option, widget)
        painter.setPen(self.border_pen)
        if self.was_moved:
            self.border_pen.setColor(QColor("#4CAF50")) 
            painter.drawRect(self.boundingRect())
        elif self.isSelected():
            self.border_pen.setColor(QColor("#FFC107"))
            painter.drawRect(self.boundingRect())
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if not self.was_moved:
            self.was_moved = True
            self.update()
