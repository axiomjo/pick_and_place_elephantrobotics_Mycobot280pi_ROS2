# In widgets_gui/graphics_gui/draggable_item_gui.py

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
        
        DEFAULT_Z = 35.0 
        DEFAULT_RX = 180.0
        DEFAULT_RY = 0.0 
        DEFAULT_RZ = 0.0

        self.pose_z = DEFAULT_Z
        self.pose_rx = DEFAULT_RX
        self.pose_ry = DEFAULT_RY

        # --- FIX #1: SPAWNING AT THE CENTER ---
        # We must manually calculate the top-left coordinate to place the center correctly.
        center_x = detected_object.center_point.x
        center_y = detected_object.center_point.y
        
        item_w = self.boundingRect().width()
        item_h = self.boundingRect().height()

        top_left_x = center_x - (item_w / 2.0)
        top_left_y = center_y - (item_h / 2.0)

        # Set the position using the calculated top-left coordinate.
        self.setPos(top_left_x, top_left_y)
        
        # We still need this so that setRotation() works around the center, not the top-left.
        self.setTransformOriginPoint(self.boundingRect().center())
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

    def get_pose(self):
        """Returns the complete 6D pose of this item."""
        # --- FIX #2: REPORTING THE CENTER ---
        # self.x() and self.y() return the top-left position. We must calculate the center.
        top_left_x = self.x()
        top_left_y = self.y()
        
        item_w = self.boundingRect().width()
        item_h = self.boundingRect().height()

        # Calculate the center from the top-left position.
        x = top_left_x + (item_w / 2.0)
        y = top_left_y + (item_h / 2.0)
        
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
