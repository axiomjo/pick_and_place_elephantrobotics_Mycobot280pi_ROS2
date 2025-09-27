
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QTextEdit,
    QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QPushButton, QMainWindow, QDockWidget, QSlider, QDoubleSpinBox, QGraphicsItem, QDialog, QGraphicsEllipseItem, QGraphicsRectItem 
)
from PyQt5.QtGui import QPixmap, QImage, QColor, QBrush, QPen, QPainterPath, QTransform
from PyQt5.QtCore import QTimer, Qt, QRectF, pyqtSignal, QObject, QPointF

class WorkingPlane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.view = QGraphicsView()
        self.working_plane_scene = QGraphicsScene()
        self.working_plane_scene.setSceneRect(QRectF(-300, -300, 600, 600))
        self.view.setScene(self.working_plane_scene)

        self.current_rotation = 0 
        self.items_on_plane = []
        
        transform = QTransform()
        transform.scale(1, -1)
        self.view.setTransform(transform)
        layout.addWidget(self.view)
        
        self.draw_mycobot280pi_working_plane()
        self.draw_axes_with_ticks()


    def draw_mycobot280pi_working_plane(self):
        
        #--- working area ----
        circle_radius = 280.0
        circle_item = QGraphicsEllipseItem(-circle_radius, -circle_radius, 2 * circle_radius, 2 * circle_radius)
        
        # Create a QColor with an alpha value (e.g., 150 for semi-transparency)
        semi_transparent_color = QColor(173, 216, 230, 50) # RGBA for lightblue with 150 alpha
        circle_item.setBrush(QBrush(QColor(semi_transparent_color)))
        circle_item.setPen(QPen(Qt.NoPen)) # Use Qt.NoPen for no outline
        circle_item.setZValue(-1) # Place it behind other items
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
        rounded_rect_item.setZValue(0)
        
        # --- robot base ---
        robotbase_radius = 45
        robotbase_item = QGraphicsEllipseItem(-robotbase_radius, -robotbase_radius, 2 * robotbase_radius, 2 * robotbase_radius)
        
        robotbase_item.setBrush(QBrush(QColor("#C3C3C3")))
        robotbase_item.setPen(QPen(Qt.NoPen))
        robotbase_item.setZValue(1) # Ensure it's on top of the rounded rectangle
        
        self.working_plane_scene.addItem(robotbase_item)
        
        face_width = 20
        face_height = 60

        face_item = QGraphicsRectItem((-face_width / 2 - 45), (-face_height / 2 ), face_width, face_height)
        
        face_item.setBrush(QBrush(QColor("#C3C3C3")))
        face_item.setPen(QPen(Qt.NoPen))
        face_item.setZValue(1)
        
        self.working_plane_scene.addItem(face_item)
        
    def draw_axes_with_ticks(self):
        # --- cartesian axes ---
        pen_axis = QPen(Qt.black, 2)
        pen_ticks = QPen(Qt.black, 1)

        # X-axis
        self.working_plane_scene.addLine(-280, 0, 280, 0, pen_axis)
        # Y-axis
        self.working_plane_scene.addLine(0, -280, 0, 280, pen_axis)

        # X ticks every 10
        for x in range(-280, 281, 10):
            if x == 0:
                continue
            length = 6 if x % 50 else 12
            self.working_plane_scene.addLine(x, -length / 2, x, length / 2, pen_ticks)

        # Y ticks every 10
        for y in range(-280, 281, 10):
            if y == 0:
                continue
            length = 6 if y % 50 else 12
            self.working_plane_scene.addLine(-length / 2, y, length / 2, y, pen_ticks)
            
            
            
       
    
    def rotate_clockwise(self):
        self.current_rotation -= 90
        self.set_pov()

    def rotate_counter_clockwise(self):
        self.current_rotation += 90
        self.set_pov()

    def set_pov(self):
        transform = QTransform()
        transform.scale(1, -1)
        transform.rotate(self.current_rotation)
        self.view.setTransform(transform)
        print(f"View rotated to {self.current_rotation % 360}°")
    
        
        

