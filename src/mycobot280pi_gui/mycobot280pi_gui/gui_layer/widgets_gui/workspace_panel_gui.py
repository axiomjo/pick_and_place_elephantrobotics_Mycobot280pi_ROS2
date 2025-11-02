"""
workspace_panel_gui.py - Defines the WorkspacePanelGUI widget.

This is the main interactive 2D canvas (the View) where the user can see
and manipulate draggable objects. It observes the WorkspaceModel for its data
and includes interactive controls for rotating selected items.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QLabel, QSlider, QDoubleSpinBox, QHBoxLayout,
    QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsPathItem, QGraphicsPixmapItem
)
from PyQt5.QtGui import (
    QTransform, QColor, QBrush, QPen, QPainterPath, QFont, QPixmap
)
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, pyqtSlot

from ...core_layer.workspace_model_core import WorkspaceModel
from .graphics_gui.draggable_item_gui import DraggableItemGUI

class InteractiveGraphicsScene(QGraphicsScene):
    selection_changed = pyqtSignal(list)
    def __init__(self, model: WorkspaceModel, parent=None):
        super().__init__(parent)
        
        self.model = model
        
        # 1. Create the dedicated item for the background
        self._background_item = QGraphicsPixmapItem()
        # 2. Set its properties as requested
        self._background_item.setZValue(-100) # Bottom-most layer
        self._background_item.setOpacity(0.25) # 25% opacity
        # 3. Make it uneditable (as requested)
        self._background_item.setFlag(QGraphicsPixmapItem.ItemIsSelectable, False)
        # 4. Add it to the scene permanently
        self.addItem(self._background_item)
        
        self.model.background_changed.connect(self.on_background_changed)
        self.model.items_changed.connect(self.on_items_changed)
        self.on_background_changed(self.model.get_background_pixmap())
        self.on_items_changed()
    
    @pyqtSlot(QPixmap)
    def on_background_changed(self, pixmap: QPixmap):
        """
        Slot to update the background pixmap when the model changes.
        """
        if pixmap.isNull():
            self._background_item.setPixmap(QPixmap()) # Clear it
            return

        # Your view is already Y-flipped, but the controller's logic
        # for object cutouts flips their pixmaps. To match, we must
        # also flip the background pixmap.
        transform = QTransform()
        transform.scale(1, -1) # Invert Y-axis
        flipped_pixmap = pixmap.transformed(transform)

        self._background_item.setPixmap(flipped_pixmap)
        
        # Position the pixmap centered at the scene's origin (0,0)
        # This matches your controller's (x - center_x) logic.
        w = flipped_pixmap.width()
        h = flipped_pixmap.height()
        self._background_item.setPos(-w / 2.0, -h / 2.0)
        
    @pyqtSlot()
    def on_items_changed(self):
        """
        Slot to update the draggable items when the model changes.
        This is the correct, robust way to sync the scene with the model.
        """
        # 1. Find and remove ALL existing DraggableItemGUI items
        # This leaves static axes and the background item untouched.
        items_to_remove = [item for item in self.items() if isinstance(item, DraggableItemGUI)]
        for item in items_to_remove:
            self.removeItem(item)
            
        # 2. Get the new list of items from the model
        items_from_model = self.model.get_all_items()
        
        # 3. Add all of them to the scene
        for item in items_from_model:
            self.addItem(item)
                
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        selected_items = [item for item in self.selectedItems() if isinstance(item, DraggableItemGUI)]
        self.selection_changed.emit(selected_items)
        
class WorkspacePanelGUI(QWidget):
    selection_changed = pyqtSignal(list)

    def __init__(self, model, parent=None): # (model: WorkspaceModel, parent: QWidget)
        super().__init__(parent)
        self.model = model

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        self.scene = InteractiveGraphicsScene(self.model, self)
        self.view = QGraphicsView(self.scene)
        self.scene.setSceneRect(QRectF(-300, -300, 600, 600))
        transform = QTransform(); transform.scale(1, -1)
        self.view.setTransform(transform)

        # --- MODIFIED: The layout is now built in steps ---
        # 1. Add the main canvas view
        main_layout.addWidget(self.view, 1) # Give it a stretch factor

        # 2. Create and add the interactive controls underneath
        rotation_controls = self._create_rotation_controls()
        main_layout.addWidget(rotation_controls)

        # 3. Draw the static background
        self.draw_mycobot280pi_working_plane()
        self.draw_axes_with_ticks()

        # Connect signals
        self.scene.selection_changed.connect(self.selection_changed)
        self.scene.selection_changed.connect(self._on_selection_changed)

        # Initial state
        self._on_selection_changed([]) # Start with controls disabled

    # --- NEW SECTION: Methods to manage interactive controls ---

    def _create_rotation_controls(self):
        """Builds the QWidget containing the rotation slider and spinbox."""
        control_container = QWidget()
        layout = QHBoxLayout(control_container)
        layout.setContentsMargins(5, 0, 5, 0)

        self.visual_rz_slider = QSlider(Qt.Horizontal)
        self.visual_rz_spinbox = QDoubleSpinBox()

        self.visual_rz_slider.setRange(-180, 180)
        self.visual_rz_spinbox.setRange(-180.0, 180.0)
        self.visual_rz_spinbox.setSuffix(" °")
        self.visual_rz_spinbox.setDecimals(1)

        # Connect slider and spinbox to each other and to the rotation logic
        self.visual_rz_slider.valueChanged.connect(self.visual_rz_spinbox.setValue)
        self.visual_rz_spinbox.valueChanged.connect(self.visual_rz_slider.setValue)
        self.visual_rz_spinbox.valueChanged.connect(self.set_selected_item_rotation)

        layout.addWidget(QLabel("Interactive Rotation (RZ):"))
        layout.addWidget(self.visual_rz_slider, 1)
        layout.addWidget(self.visual_rz_spinbox)

        return control_container

    @pyqtSlot(list)
    def _on_selection_changed(self, selected_items):
        """Enables/disables controls and updates them with the selected item's rotation."""
        if len(selected_items) == 1:
            item = selected_items[0]
            self.visual_rz_slider.setEnabled(True)
            self.visual_rz_spinbox.setEnabled(True)
            
            # Update the slider/spinbox value without triggering its own signal
            self.visual_rz_spinbox.blockSignals(True)
            self.visual_rz_slider.blockSignals(True)
            self.visual_rz_spinbox.setValue(item.rotation())
            self.visual_rz_spinbox.blockSignals(False)
            self.visual_rz_slider.blockSignals(False)
        else:
            # If nothing or multiple items are selected, disable the controls
            self.visual_rz_slider.setEnabled(False)
            self.visual_rz_spinbox.setEnabled(False)

    @pyqtSlot(float)
    def set_selected_item_rotation(self, angle):
        """Applies the rotation to the currently selected item."""
        selected_items = self.scene.selectedItems()
        if len(selected_items) == 1 and isinstance(selected_items[0], DraggableItemGUI):
            selected_items[0].setRotation(float(angle))
            


    @pyqtSlot()
    def rotate_selected_clockwise(self):
        """Rotates the entire VIEW clockwise by 15 degrees."""
        self.view.rotate(-15)

    @pyqtSlot()
    def rotate_selected_counter_clockwise(self):
        """Rotates the entire VIEW counter-clockwise by 15 degrees."""
        self.view.rotate(15)
        
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
        self.scene.addItem(circle_item)

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
        self.scene.addItem(path_item)

        # --- 7. inner blocked area (gray center) ---
        base_block_item = QGraphicsEllipseItem(
            -INNER_RADIUS, -INNER_RADIUS, 2 * INNER_RADIUS, 2 * INNER_RADIUS
        )
        base_block_item.setBrush(QBrush(QColor(192, 192, 192, 150)))
        base_block_item.setPen(QPen(Qt.NoPen))
        base_block_item.setZValue(1)
        self.scene.addItem(base_block_item)

        # --- baseplate rectangle ---
        rect_width, rect_height, corner_radius = 110, 150, 7.5
        path = QPainterPath()
        path.addRoundedRect(
            QRectF(-rect_width / 2, -rect_height / 2, rect_width, rect_height),
            corner_radius,
            corner_radius,
        )
        rounded_rect_item = self.scene.addPath(path)
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
        self.scene.addItem(robotbase_item)

        # --- robot base face ---
        face_width, face_height = 20, 60
        face_item = QGraphicsRectItem(
            -face_width / 2 - 45, -face_height / 2, face_width, face_height
        )
        face_item.setBrush(QBrush(QColor("#C3C3C3")))
        face_item.setPen(QPen(Qt.NoPen))
        face_item.setZValue(2)
        self.scene.addItem(face_item)


    def draw_axes_with_ticks(self):
        """Draw coordinate grid with labeled axes."""
        grid_range = 300
        pen_grid = QPen(QColor(220, 220, 220), 1, Qt.SolidLine)

        # grid lines
        for x in range(-grid_range, grid_range + 1, 10):
            self.scene.addLine(
                x, -grid_range, x, grid_range, pen_grid
            ).setZValue(-10)

        for y in range(-grid_range, grid_range + 1, 10):
            self.scene.addLine(
                -grid_range, y, grid_range, y, pen_grid
            ).setZValue(-10)

        # axes
        pen_x_axis = QPen(Qt.red, 2)
        pen_y_axis = QPen(Qt.blue, 2)
        self.scene.addLine(
            -grid_range, 0, grid_range, 0, pen_x_axis
        ).setZValue(5)
        self.scene.addLine(
            0, -grid_range, 0, grid_range, pen_y_axis
        ).setZValue(5)

        # ticks
        tick_size = 5
        for val in range(-grid_range, grid_range + 1, 50):
            if val == 0:
                continue
            self.scene.addLine(
                val, -tick_size, val, tick_size, pen_x_axis
            ).setZValue(6)
            self.scene.addLine(
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
            self.scene.addItem(text_x)

            text_y = QGraphicsTextItem(str(val))
            text_y.setFont(font)
            text_y.setDefaultTextColor(Qt.blue)
            text_y.setPos(-40, val + 7)
            text_y.setTransform(text_transform)
            text_y.setZValue(7)
            self.scene.addItem(text_y)

        # origin dot
        origin = self.scene.addEllipse(
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
        self.scene.addItem(x_label)

        x_label_neg = QGraphicsTextItem("−X")
        x_label_neg.setFont(font_big)
        x_label_neg.setDefaultTextColor(Qt.red)
        x_label_neg.setPos(-grid_range - 50, 20)
        x_label_neg.setTransform(text_transform)
        x_label_neg.setZValue(9)
        self.scene.addItem(x_label_neg)

        y_label = QGraphicsTextItem("Y")
        y_label.setFont(font_big)
        y_label.setDefaultTextColor(Qt.blue)
        y_label.setPos(-15, grid_range + 50)
        y_label.setTransform(text_transform)
        y_label.setZValue(9)
        self.scene.addItem(y_label)

        y_label_neg = QGraphicsTextItem("−Y")
        y_label_neg.setFont(font_big)
        y_label_neg.setDefaultTextColor(Qt.blue)
        y_label_neg.setPos(-20, -grid_range)
        y_label_neg.setTransform(text_transform)
        y_label_neg.setZValue(9)
        self.scene.addItem(y_label_neg)
