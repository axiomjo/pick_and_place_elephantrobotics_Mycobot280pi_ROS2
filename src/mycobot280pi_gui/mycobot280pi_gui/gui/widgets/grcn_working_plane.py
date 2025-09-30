
"""
Defines the WorkingPlane widget.

This widget provides the main interactive 2D canvas for the application.
It uses a QGraphicsScene to display a representation of the robot's workspace,
including its base, reachable area, and a coordinate grid.

It is the container for all DraggableItem instances, allowing the user to
visually arrange objects for the pick-and-place task. It is a self-contained
component controlled by the MainWindow.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsTextItem
)
from PyQt5.QtGui import (
    QTransform,
    QColor,
    QBrush,
    QPen,
    QPainterPath,
    QFont
)
from PyQt5.QtCore import Qt, QRectF

# The only internal dependency is the DraggableItem it will contain.
from .grcn_draggable_item import DraggableItem


class WorkingPlane(QWidget):
    """A widget that displays a 2D scene representing the robot's workspace."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = QGraphicsView()
        self.working_plane_scene = QGraphicsScene()
        self.working_plane_scene.setSceneRect(QRectF(-300, -300, 600, 600))
        self.view.setScene(self.working_plane_scene)

        # A list to hold references to the DraggableItems for easy access
        self.items_on_plane = []
        
        # Invert the Y-axis to have a standard Cartesian coordinate system (Y increases upwards)
        transform = QTransform()
        transform.scale(1, -1)
        self.view.setTransform(transform)
        
        layout.addWidget(self.view)
        
        self.draw_mycobot280pi_working_plane()
        self.draw_axes_with_ticks()

    def draw_mycobot280pi_working_plane(self):
        """Draws the static elements representing the robot base and work area."""
        # Working area (280 mm radius, semi-transparent)
        circle_radius = 280.0
        circle_item = QGraphicsEllipseItem(-circle_radius, -circle_radius,
                                           2 * circle_radius, 2 * circle_radius)
        semi_transparent_color = QColor(173, 216, 230, 50)
        circle_item.setBrush(QBrush(semi_transparent_color))
        circle_item.setPen(QPen(Qt.NoPen))
        circle_item.setZValue(0)
        self.working_plane_scene.addItem(circle_item)

        # --- baseplate ----
        rect_width = 110
        rect_height = 150
        corner_radius =  7.5
        
        rectangle_item = QGraphicsRectItem((-rect_width / 2), (-rect_height / 2), rect_width, rect_height)
        rectangle_item.setRect(QRectF((-rect_width / 2), (-rect_height / 2), rect_width, rect_height))

        path = QPainterPath()
        path.addRoundedRect(QRectF((-rect_width / 2), (-rect_height / 2), rect_width, rect_height), corner_radius, corner_radius)
        
        rounded_rect_item = self.working_plane_scene.addPath(path)
        rounded_rect_item.setBrush(QBrush(QColor("#DFDFDF")))
        rounded_rect_item.setPen(QPen(Qt.NoPen))
        rounded_rect_item.setZValue(1)
        
        # --- robot base & base face ---
        robotbase_radius = 45
        robotbase_item = QGraphicsEllipseItem(-robotbase_radius, -robotbase_radius, 2 * robotbase_radius, 2 * robotbase_radius)
        
        robotbase_item.setBrush(QBrush(QColor("#C3C3C3")))
        robotbase_item.setPen(QPen(Qt.NoPen))
        robotbase_item.setZValue(2) # Ensure it's on top of the rounded rectangle
        
        self.working_plane_scene.addItem(robotbase_item)
        
        face_width = 20
        face_height = 60

        face_item = QGraphicsRectItem((-face_width / 2 - 45), (-face_height / 2 ), face_width, face_height)
        
        face_item.setBrush(QBrush(QColor("#C3C3C3")))
        face_item.setPen(QPen(Qt.NoPen))
        face_item.setZValue(2)
        
        self.working_plane_scene.addItem(face_item)
        

    def draw_axes_with_ticks(self):
        grid_range = 300  # since scene is -300..+300

        # --- Grid lines (solid, behind everything) ---
        pen_grid = QPen(QColor(220, 220, 220), 1, Qt.SolidLine)
        for x in range(-grid_range, grid_range + 1, 10):
            self.working_plane_scene.addLine(x, -grid_range, x, grid_range, pen_grid).setZValue(-10)
        for y in range(-grid_range, grid_range + 1, 10):
            self.working_plane_scene.addLine(-grid_range, y, grid_range, y, pen_grid).setZValue(-10)

        # --- Axes ---
        pen_x_axis = QPen(Qt.red, 2)
        pen_y_axis = QPen(Qt.blue, 2)
        self.working_plane_scene.addLine(-grid_range, 0, grid_range, 0, pen_x_axis).setZValue(5)
        self.working_plane_scene.addLine(0, -grid_range, 0, grid_range, pen_y_axis).setZValue(5)

        # --- Ticks every 50 units ---
        tick_size = 5
        
        for val in range(-grid_range, grid_range + 1, 50):
            if val == 0:
                continue
            # X-axis ticks
            self.working_plane_scene.addLine(val, -tick_size, val, tick_size, pen_x_axis).setZValue(6)
            # Y-axis ticks
            self.working_plane_scene.addLine(-tick_size, val, tick_size, val, pen_y_axis).setZValue(6)
      
        # --- Numeric labels ---
        font = QFont("Arial", 8)
        text_transform = QTransform().scale(1, -1)
        
        for val in range(-grid_range + 50, grid_range, 50):
            if val == 0:
                continue
                
            # X-axis labels
            text_x = QGraphicsTextItem(str(val))
            text_x.setFont(font)
            text_x.setDefaultTextColor(Qt.red)
            text_x.setPos(val-15, -10)
            text_x.setTransform(text_transform)
            text_x.setZValue(7)
            self.working_plane_scene.addItem(text_x)
            
            # Y-axis labels
            text_y = QGraphicsTextItem(str(val))
            text_y.setFont(font)
            text_y.setDefaultTextColor(Qt.blue)
            text_y.setPos(-40, val +7)
            text_y.setTransform(text_transform)
            text_y.setZValue(7)
            self.working_plane_scene.addItem(text_y)
            
        # --- Origin marker ---
        origin = self.working_plane_scene.addEllipse(
            -3, -3, 6, 6, QPen(Qt.red), QBrush(Qt.red)
        )
        origin.setZValue(8)
        
        # --- Big axis markers ---
        font_big = QFont("Arial", 20, QFont.Bold)

        x_label = QGraphicsTextItem("X")
        x_label.setFont(font_big)
        x_label.setDefaultTextColor(Qt.red)
        x_label.setPos(grid_range , 20)
        x_label.setTransform(text_transform)
        x_label.setZValue(9)
        self.working_plane_scene.addItem(x_label)
        
        x_label_neg = QGraphicsTextItem("−X")
        x_label_neg.setFont(font_big)
        x_label_neg.setDefaultTextColor(Qt.red)
        x_label_neg.setPos(-grid_range - 50, 20)
        x_label_neg.setTransform(text_transform)
        x_label_neg.setZValue(9)
        self.working_plane_scene.addItem(x_label_neg)
        
        y_label = QGraphicsTextItem("Y")
        y_label.setFont(font_big)
        y_label.setDefaultTextColor(Qt.blue)
        y_label.setPos(-15, grid_range + 50)
        y_label.setTransform(text_transform)
        y_label.setZValue(9)
        self.working_plane_scene.addItem(y_label)

        y_label_neg = QGraphicsTextItem("−Y")
        y_label_neg.setFont(font_big)
        y_label_neg.setDefaultTextColor(Qt.blue)
        y_label_neg.setPos(- 20, -grid_range)
        y_label_neg.setTransform(text_transform)
        y_label_neg.setZValue(9)
        self.working_plane_scene.addItem(y_label_neg)




          
    def reset_scene(self):
        """Clears all DraggableItems from the scene and redraws the background."""
        # A more efficient way to clear only the draggable items
        for item in self.items_on_plane:
            self.working_plane_scene.removeItem(item)
        self.items_on_plane.clear()

    def rotate_clockwise(self):
        """Rotates the entire view clockwise by 15 degrees."""
        self.view.rotate(15)

    def rotate_counter_clockwise(self):
        """Rotates the entire view counter-clockwise by 15 degrees."""
        self.view.rotate(-15)
        
    def set_selected_items_rotation(self, angle: float):
        """Sets the absolute rotation for all currently selected DraggableItems."""
        selected_items = self.working_plane_scene.selectedItems()
        for item in selected_items:
            if isinstance(item, DraggableItem):
                item.setRotation(float(angle))
