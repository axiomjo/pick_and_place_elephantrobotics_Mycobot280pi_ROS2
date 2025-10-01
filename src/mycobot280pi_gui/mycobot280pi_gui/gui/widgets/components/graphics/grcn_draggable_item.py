
"""
Defines the DraggableItem class for the QGraphicsScene.

This class represents a single, interactive object on the WorkingPlane.
It is a QGraphicsPixmapItem, not a QWidget, and is designed to be added
to a QGraphicsScene.

Key features:
- It can be moved and selected by the user.
- It stores the original ROS message data for the detected object.
- It provides custom visual feedback (a colored border) based on its state.
"""

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt5.QtCore import Qt

# Type hinting for the constructor
from mycobot280pi_interfaces.msg import OneDetectedObject


class DraggableItem(QGraphicsPixmapItem):
    """A QGraphicsPixmapItem that can be moved, selected, and rotated."""

    def __init__(self, pixmap: QPixmap, detected_object: OneDetectedObject, parent=None):
        super().__init__(pixmap, parent)
        
        # Store the original data from the vision node
        self.detected_object = detected_object
        self.object_id = detected_object.id
        
        # State flag to track if the user has interacted with this item
        self.was_moved = False
        
        # Enable item interactivity
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable
        )
        
        # Set a helpful cursor for better user experience
        self.setCursor(Qt.PointingHandCursor)
        
        # Initialize the pen for drawing the border
        self.border_pen = QPen(Qt.transparent)
        self.border_pen.setWidth(4)
        
        # Set the origin for transformations (like rotation) to the item's center
        self.setTransformOriginPoint(self.boundingRect().center())
        
    def paint(self, painter: QPainter, option, widget):
        """
        Overrides the default paint method to draw a border when the
        item is selected or has been moved.
        """
        # First, draw the original pixmap
        super().paint(painter, option, widget)
        
        # Then, draw a border on top based on the item's state
        painter.setPen(self.border_pen)
        if self.was_moved:
            self.border_pen.setColor(QColor("#4CAF50")) # Green for moved
            painter.drawRect(self.boundingRect())
        elif self.isSelected():
            self.border_pen.setColor(QColor("#FFC107")) # Amber/Gold for selected
            painter.drawRect(self.boundingRect())
    
    def mouseReleaseEvent(self, event):
        """
        Overrides the mouse release event to update the 'was_moved' state.
        """
        # Call the parent method to ensure default behavior (like stopping movement)
        super().mouseReleaseEvent(event)
        
        # If this is the first time the item has been moved, set the flag
        if not self.was_moved:
            self.was_moved = True
            # Force a repaint to show the new 'moved' (green) border
            self.update()
