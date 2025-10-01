"""
Defines the WorkspacePlane widget, the main interactive 2D canvas.
This version is self-contained, including its own controls for rotation.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, QFrame,
    QLabel, QSlider, QDoubleSpinBox, QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsRectItem
)
from PyQt5.QtGui import (
    QTransform, QColor, QBrush, QPen, QPainterPath, QFont
)
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, pyqtSlot

# Pastikan path import ini benar
from .components.graphics.grcn_draggable_item import DraggableItem

class InteractiveGraphicsScene(QGraphicsScene):
    item_selected = pyqtSignal(object)
    selection_cleared = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        selected_items = self.selectedItems()
        if len(selected_items) == 1: self.item_selected.emit(selected_items[0])
        elif len(selected_items) == 0: self.selection_cleared.emit()


class WorkspacePlane(QWidget):
    item_selected = pyqtSignal(object)
    selection_cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        self.working_plane_scene = InteractiveGraphicsScene(self)
        self.view = QGraphicsView(self.working_plane_scene)
        self.working_plane_scene.setSceneRect(QRectF(-300, -300, 600, 600))
        
        self.working_plane_scene.item_selected.connect(self._on_item_selected)
        self.working_plane_scene.selection_cleared.connect(self._on_selection_cleared)
        
        self.items_on_plane = []
        
        transform = QTransform(); transform.scale(1, -1)
        self.view.setTransform(transform)
        
        # ### INI ADALAH STRUKTUR YANG BENAR ###
        # 1. Tambahkan view (kanvas) ke layout
        main_layout.addWidget(self.view, 1)

        # 2. Buat dan tambahkan panel kontrol di bawahnya
        rotation_controls = self._create_rotation_controls()
        main_layout.addWidget(rotation_controls)
        
        # 3. Baru gambar isinya
        self.draw_mycobot280pi_working_plane()
        self.draw_axes_with_ticks()

        self._on_selection_cleared()
    
    def _create_rotation_controls(self):
        control_container = QWidget()
        layout = QHBoxLayout(control_container)
        layout.setContentsMargins(5, 0, 5, 0)

        self.visual_rz_slider = QSlider(Qt.Horizontal)
        self.visual_rz_spinbox = QDoubleSpinBox()

        self.visual_rz_spinbox.setRange(-180.0, 180.0); self.visual_rz_slider.setRange(-180, 180)
        self.visual_rz_spinbox.setSuffix(" °")
        self.visual_rz_spinbox.setDecimals(1)

        self.visual_rz_slider.valueChanged.connect(self.visual_rz_spinbox.setValue)
        self.visual_rz_spinbox.valueChanged.connect(self.visual_rz_slider.setValue)
        self.visual_rz_spinbox.valueChanged.connect(self.set_selected_item_rotation)

        layout.addWidget(QLabel("Interactive Rotation (RZ):"))
        layout.addWidget(self.visual_rz_slider, 1)
        layout.addWidget(self.visual_rz_spinbox)

        return control_container

    def _set_synced_rotation_value(self, angle):
        self.visual_rz_spinbox.blockSignals(True)
        self.visual_rz_slider.blockSignals(True)
        self.visual_rz_spinbox.setValue(angle)
        self.visual_rz_spinbox.blockSignals(False)
        self.visual_rz_slider.blockSignals(False)
        
    @pyqtSlot(object)
    def _on_item_selected(self, item):
        self.visual_rz_slider.setEnabled(True)
        self.visual_rz_spinbox.setEnabled(True)
        self._set_synced_rotation_value(item.rotation())
        self.item_selected.emit(item)

    @pyqtSlot()
    def _on_selection_cleared(self):
        self.visual_rz_slider.setEnabled(False)
        self.visual_rz_spinbox.setEnabled(False)
        self.selection_cleared.emit()
    
    @pyqtSlot(float)
    def set_selected_item_rotation(self, angle: float):
        selected_items = self.working_plane_scene.selectedItems()
        for item in selected_items:
            if isinstance(item, DraggableItem):
                item.setRotation(float(angle))
    
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
        


    # ### DIKEMBALIKAN: Kembali ke loop for yang lebih jelas dan stabil ###
    def draw_axes_with_ticks(self):
        grid_range = 300
        pen_grid = QPen(QColor(220, 220, 220), 1, Qt.SolidLine)
        for x in range(-grid_range, grid_range + 1, 10): self.working_plane_scene.addLine(x, -grid_range, x, grid_range, pen_grid).setZValue(-10)
        for y in range(-grid_range, grid_range + 1, 10): self.working_plane_scene.addLine(-grid_range, y, grid_range, y, pen_grid).setZValue(-10)

        pen_x_axis = QPen(Qt.red, 2)
        pen_y_axis = QPen(Qt.blue, 2)
        self.working_plane_scene.addLine(-grid_range, 0, grid_range, 0, pen_x_axis).setZValue(5)
        self.working_plane_scene.addLine(0, -grid_range, 0, grid_range, pen_y_axis).setZValue(5)

        tick_size = 5
        for val in range(-grid_range, grid_range + 1, 50):
            if val == 0: continue
            self.working_plane_scene.addLine(val, -tick_size, val, tick_size, pen_x_axis).setZValue(6)
            self.working_plane_scene.addLine(-tick_size, val, tick_size, val, pen_y_axis).setZValue(6)
    
        font = QFont("Arial", 8)
        text_transform = QTransform().scale(1, -1)
        for val in range(-grid_range + 50, grid_range, 50):
            if val == 0: continue
            text_x = QGraphicsTextItem(str(val)); text_x.setFont(font); text_x.setDefaultTextColor(Qt.red); text_x.setPos(val-15, -10)
            text_x.setTransform(text_transform); text_x.setZValue(7); self.working_plane_scene.addItem(text_x)
            text_y = QGraphicsTextItem(str(val)); text_y.setFont(font); text_y.setDefaultTextColor(Qt.blue); text_y.setPos(-40, val + 7)
            text_y.setTransform(text_transform); text_y.setZValue(7); self.working_plane_scene.addItem(text_y)
            
        origin = self.working_plane_scene.addEllipse(-3, -3, 6, 6, QPen(Qt.red), QBrush(Qt.red)); origin.setZValue(8)
        
        font_big = QFont("Arial", 20, QFont.Bold)
        x_label = QGraphicsTextItem("X"); x_label.setFont(font_big); x_label.setDefaultTextColor(Qt.red); x_label.setPos(grid_range , 20)
        x_label.setTransform(text_transform); x_label.setZValue(9); self.working_plane_scene.addItem(x_label)
        x_label_neg = QGraphicsTextItem("−X"); x_label_neg.setFont(font_big); x_label_neg.setDefaultTextColor(Qt.red); x_label_neg.setPos(-grid_range - 50, 20)
        x_label_neg.setTransform(text_transform); x_label_neg.setZValue(9); self.working_plane_scene.addItem(x_label_neg)
        y_label = QGraphicsTextItem("Y"); y_label.setFont(font_big); y_label.setDefaultTextColor(Qt.blue); y_label.setPos(-15, grid_range + 50)
        y_label.setTransform(text_transform); y_label.setZValue(9); self.working_plane_scene.addItem(y_label)
        y_label_neg = QGraphicsTextItem("−Y"); y_label_neg.setFont(font_big); y_label_neg.setDefaultTextColor(Qt.blue); y_label_neg.setPos(- 20, -grid_range)
        y_label_neg.setTransform(text_transform); y_label_neg.setZValue(9); self.working_plane_scene.addItem(y_label_neg)

    def reset_scene(self):
        for item in self.items_on_plane: self.working_plane_scene.removeItem(item)
        self.items_on_plane.clear()
        
        
    def rotate_clockwise(self):
        """Memutar seluruh TAMPILAN (view) searah jarum jam."""
        self.view.rotate(15)

    def rotate_counter_clockwise(self):
        """Memutar seluruh TAMPILAN (view) berlawanan arah jarum jam."""
        self.view.rotate(-15)

