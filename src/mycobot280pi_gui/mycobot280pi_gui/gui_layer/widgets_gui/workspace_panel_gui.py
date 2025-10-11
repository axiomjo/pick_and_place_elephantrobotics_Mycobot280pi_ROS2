"""
workspace_panel_gui.py - Defines the WorkspacePanelGUI widget.

This is the main interactive 2D canvas (the View) where the user can see
and manipulate draggable objects. It observes the WorkspaceModel for its data.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QFrame,
    QLabel, QSlider, QDoubleSpinBox, QGraphicsTextItem,
    QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsPathItem
)
from PyQt5.QtGui import (
    QTransform, QColor, QBrush, QPen, QPainterPath, QFont
)
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, pyqtSlot
from typing import List

# Import the model it observes and the graphics it displays
from ...core_layer.workspace_model_core import WorkspaceModel
from .graphics_gui.draggable_item_gui import DraggableItemGUI

# --- Custom Scene for emitting selection signals ---
class InteractiveGraphicsScene(QGraphicsScene):
    """A QGraphicsScene that emits signals on selection changes."""
    # Emits a list of the currently selected DraggableItemGUI objects
    selection_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        selected_items = [item for item in self.selectedItems() if isinstance(item, DraggableItemGUI)]
        self.selection_changed.emit(selected_items)


# --- The Main Workspace Panel Widget ---
class WorkspacePanelGUI(QWidget):
    """The main View for the interactive workspace."""
    
    # This signal is forwarded from the scene for other UI components to use.
    selection_changed = pyqtSignal(list)

    def __init__(self, model, parent=None): # (model: WorkspaceModel, parent: QWidget)
        super().__init__(parent)
        
        # --- Dependency (Injected) ---
        self.model = model

        # This list holds references to items CURRENTLY displayed in the scene.
        # It is managed exclusively by the update_display slot.
        self._scene_items = []

        # --- UI Setup ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scene = InteractiveGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.scene.setSceneRect(QRectF(-300, -300, 600, 600))
        
        # Flip the Y-axis to have a standard mathematical coordinate system
        transform = QTransform()
        transform.scale(1, -1)
        self.view.setTransform(transform)

        main_layout.addWidget(self.view)

        # Draw the static background elements once
        self.draw_mycobot280pi_working_plane()
        self.draw_axes_with_ticks()

        # --- Signal Connections ---
        # Connect to the model to receive updates
        self.model.items_changed.connect(self.update_display)
        # Forward selection changes from the scene
        self.scene.selection_changed.connect(self.selection_changed)

        # Perform an initial draw
        self.update_display()

    @pyqtSlot()
    def update_display(self):
        """
        Public slot to redraw the scene based on the model's current state.
        This is the core of the View's responsibility.
        """
        # 1. Remove all old draggable items from the scene
        for item in self._scene_items:
            self.scene.removeItem(item)
        self._scene_items.clear()

        # 2. Get the new, authoritative list of items from the model
        items_from_model = self.model.get_all_items()

        # 3. Add the new items to the scene and our internal tracker
        for item in items_from_model:
            self.scene.addItem(item)
            self._scene_items.append(item)
            
            # Reposition the item based on its internal state.
            # This is important as the item's position might have been set
            # before it was added to the scene.
            center_pos = item.mapToScene(item.boundingRect().center())
            img_height, img_width = item.pixmap().height(), item.pixmap().width()
            cam_center_x = img_width / 2.0
            cam_center_y = img_height / 2.0

            scene_x = item.detected_object.center_point.x - cam_center_x
            scene_y = -(item.detected_object.center_point.y - cam_center_y)
            final_x = scene_x - (img_width / 2)
            final_y = scene_y - (img_height / 2)
            item.setPos(final_x, final_y)


    # --- Methods for drawing static elements (copied from old project) ---

    def draw_mycobot280pi_working_plane(self):
        """Draws the static elements representing the robot base and work area."""

        # --- main working circle (soft background) ---
        circle_radius = 280.0
        circle_item = QGraphicsEllipseItem(
            -circle_radius, -circle_radius, 2 * circle_radius, 2 * circle_radius
        )
        semi_transparent_color = QColor(173, 216, 230, 50)
        circle_item.setBrush(QBrush(semi_transparent_color))
        circle_item.setPen(QPen(Qt.NoPen))
        circle_item.setZValue(0)
        self.working_plane_scene.addItem(circle_item)

        OUTER_RADIUS = 250
        INNER_RADIUS = 150

        # --- 1. outer ring (radius 250mm) ---
        outer_circle = QPainterPath()
        outer_circle.addEllipse(
            -OUTER_RADIUS, -OUTER_RADIUS, 2 * OUTER_RADIUS, 2 * OUTER_RADIUS
        )

        # --- 2. inner circle (excluded center area) ---
        inner_circle = QPainterPath()
        inner_circle.addEllipse(
            -INNER_RADIUS, -INNER_RADIUS, 2 * INNER_RADIUS, 2 * INNER_RADIUS
        )

        # --- 3. blocked area behind robot ---
        block_width = 250.0
        block_height = 500.0
        X_START_BLOCK = -OUTER_RADIUS
        X_END_BLOCK = -50.0

        block_area = QPainterPath()
        block_area.addRect(
            X_START_BLOCK,
            -block_height / 2,
            X_END_BLOCK - X_START_BLOCK,
            block_height,
        )

        # --- 4–5. combine paths into "C" shape ---
        ring_path = outer_circle.subtracted(inner_circle)
        c_shape_path = ring_path.subtracted(block_area)

        # --- 6. style the C-shaped working area ---
        path_item = QGraphicsPathItem(c_shape_path)
        semi_transparent_color = QColor(173, 216, 230, 80)
        path_item.setBrush(QBrush(semi_transparent_color))
        path_item.setPen(QPen(Qt.NoPen))
        path_item.setZValue(0)
        self.working_plane_scene.addItem(path_item)

        # --- 7. inner blocked area (gray center) ---
        base_block_item = QGraphicsEllipseItem(
            -INNER_RADIUS, -INNER_RADIUS, 2 * INNER_RADIUS, 2 * INNER_RADIUS
        )
        base_block_item.setBrush(QBrush(QColor(192, 192, 192, 150)))
        base_block_item.setPen(QPen(Qt.NoPen))
        base_block_item.setZValue(1)
        self.working_plane_scene.addItem(base_block_item)

        # --- baseplate rectangle ---
        rect_width, rect_height, corner_radius = 110, 150, 7.5
        path = QPainterPath()
        path.addRoundedRect(
            QRectF(-rect_width / 2, -rect_height / 2, rect_width, rect_height),
            corner_radius,
            corner_radius,
        )
        rounded_rect_item = self.working_plane_scene.addPath(path)
        rounded_rect_item.setBrush(QBrush(QColor("#DFDFDF")))
        rounded_rect_item.setPen(QPen(Qt.NoPen))
        rounded_rect_item.setZValue(1)

    # --- robot base ---
    robotbase_radius = 45
    robotbase_item = QGraphicsEllipseItem(
        -robotbase_radius, -robotbase_radius,
        2 * robotbase_radius, 2 * robotbase_radius
    )
    robotbase_item.setBrush(QBrush(QColor("#C3C3C3")))
    robotbase_item.setPen(QPen(Qt.NoPen))
    robotbase_item.setZValue(2)
    self.working_plane_scene.addItem(robotbase_item)

    # --- robot base face ---
    face_width, face_height = 20, 60
    face_item = QGraphicsRectItem(
        -face_width / 2 - 45, -face_height / 2, face_width, face_height
    )
    face_item.setBrush(QBrush(QColor("#C3C3C3")))
    face_item.setPen(QPen(Qt.NoPen))
    face_item.setZValue(2)
    self.working_plane_scene.addItem(face_item)


def draw_axes_with_ticks(self):
    """Draw coordinate grid with labeled axes."""
    grid_range = 300
    pen_grid = QPen(QColor(220, 220, 220), 1, Qt.SolidLine)

    # grid lines
    for x in range(-grid_range, grid_range + 1, 10):
        self.working_plane_scene.addLine(
            x, -grid_range, x, grid_range, pen_grid
        ).setZValue(-10)

    for y in range(-grid_range, grid_range + 1, 10):
        self.working_plane_scene.addLine(
            -grid_range, y, grid_range, y, pen_grid
        ).setZValue(-10)

    # axes
    pen_x_axis = QPen(Qt.red, 2)
    pen_y_axis = QPen(Qt.blue, 2)
    self.working_plane_scene.addLine(
        -grid_range, 0, grid_range, 0, pen_x_axis
    ).setZValue(5)
    self.working_plane_scene.addLine(
        0, -grid_range, 0, grid_range, pen_y_axis
    ).setZValue(5)

    # ticks
    tick_size = 5
    for val in range(-grid_range, grid_range + 1, 50):
        if val == 0:
            continue
        self.working_plane_scene.addLine(
            val, -tick_size, val, tick_size, pen_x_axis
        ).setZValue(6)
        self.working_plane_scene.addLine(
            -tick_size, val, tick_size, val, pen_y_axis
        ).setZValue(6)

    # labels
    font = QFont("Arial", 8)
    text_transform = QTransform().scale(1, -1)

    for val in range(-grid_range + 50, grid_range, 50):
        if val == 0:
            continue

        text_x = QGraphicsTextItem(str(val))
        text_x.setFont(font)
        text_x.setDefaultTextColor(Qt.red)
        text_x.setPos(val - 15, -10)
        text_x.setTransform(text_transform)
        text_x.setZValue(7)
        self.working_plane_scene.addItem(text_x)

        text_y = QGraphicsTextItem(str(val))
        text_y.setFont(font)
        text_y.setDefaultTextColor(Qt.blue)
        text_y.setPos(-40, val + 7)
        text_y.setTransform(text_transform)
        text_y.setZValue(7)
        self.working_plane_scene.addItem(text_y)

    # origin dot
    origin = self.working_plane_scene.addEllipse(
        -3, -3, 6, 6, QPen(Qt.red), QBrush(Qt.red)
    )
    origin.setZValue(8)

    # big axis labels
    font_big = QFont("Arial", 20, QFont.Bold)
    text_transform = QTransform().scale(1, -1)

    x_label = QGraphicsTextItem("X")
    x_label.setFont(font_big)
    x_label.setDefaultTextColor(Qt.red)
    x_label.setPos(grid_range, 20)
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
    y_label_neg.setPos(-20, -grid_range)
    y_label_neg.setTransform(text_transform)
    y_label_neg.setZValue(9)
    self.working_plane_scene.addItem(y_label_neg)

