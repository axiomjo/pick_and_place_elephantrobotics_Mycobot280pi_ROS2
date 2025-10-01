#!/usr/bin/env python3

"""
Defines the PointHandle class.

This is a simple, reusable QGraphicsItem that represents a draggable handle
(a small circle) within a QGraphicsScene. It is used by widgets like the
PerspectiveEditorWidget to allow users to select points interactively.
"""

from PyQt5.QtWidgets import QGraphicsEllipseItem
from PyQt5.QtGui import QColor, QBrush


class PointHandle(QGraphicsEllipseItem):
    """A draggable ellipse item used as an interactive handle in a scene."""
    
    def __init__(self, x: float, y: float, radius: int = 8, color: QColor = QColor("red")):
        """
        Initializes a handle at a specific position.
        
        Args:
            x: The initial x-coordinate in the scene.
            y: The initial y-coordinate in the scene.
            radius: The radius of the handle's circle.
            color: The fill color of the handle.
        """
        # Create the ellipse centered at (0, 0)
        super().__init__(-radius/2, -radius/2, radius, radius)
        
        self.setBrush(QBrush(color))
        self.setPen(QColor("white")) # Add a white border for visibility
        
        # Set flags to make the handle interactive
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsScenePositionChanges, True)
        
        # Move the handle to its initial position in the scene
        self.setPos(x, y)

    def get_point(self):
        """
        Returns the handle's current position as a tuple of integers.
        
        Returns:
            A tuple containing the (x, y) coordinates.
        """
        return int(self.pos().x()), int(self.pos().y())
