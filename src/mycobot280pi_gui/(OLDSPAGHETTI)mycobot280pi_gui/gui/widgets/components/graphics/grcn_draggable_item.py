"""
Defines the DraggableItem class for the QGraphicsScene.

Refactored to match the OneDetectedObject.msg definition. It uses x, y from the
message and applies sensible defaults for the missing 3D pose data (z, rx, ry, rz).
"""

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt5.QtCore import Qt

# Type hinting for the constructor
from mycobot280pi_interfaces.msg import OneDetectedObject

class DraggableItem(QGraphicsPixmapItem):
    """A QGraphicsPixmapItem that can be moved, selected, rotated, and reports its 6D pose."""

    def __init__(self, pixmap: QPixmap, detected_object: OneDetectedObject, parent=None):
        super().__init__(pixmap, parent)
        
        self.detected_object = detected_object
        self.object_id = detected_object.id
        
        # ### PERUBAHAN UTAMA DI SINI ###
        # Kita sekarang menggunakan nilai default untuk data yang tidak ada di pesan ROS.
        
        # Nilai default untuk Z (misalnya, ketinggian aman di atas meja)
        DEFAULT_Z = 48.0 
        # Nilai default untuk rotasi (misalnya, gripper menghadap lurus ke bawah)
        DEFAULT_RX = 180.0
        DEFAULT_RY = 0.0
        # Untuk RZ, kita bisa mulai dari 0 atau dari data lain jika ada
        DEFAULT_RZ = 0.0

        # Simpan komponen pose 3D statis (menggunakan nilai default)
        self.pose_z = DEFAULT_Z
        self.pose_rx = DEFAULT_RX
        self.pose_ry = DEFAULT_RY

        # Atur pose 2D awal dari pesan ROS
        # Kita asumsikan center_point memiliki atribut .x dan .y
        self.setPos(detected_object.center_point.x, detected_object.center_point.y)
        self.setRotation(DEFAULT_RZ)
        
        self.was_moved = False
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        self.setCursor(Qt.PointingHandCursor)
        self.border_pen = QPen(Qt.transparent); self.border_pen.setWidth(4)
        self.setTransformOriginPoint(self.boundingRect().center())

    def get_pose(self):
        """
        Mengembalikan pose 6D lengkap dari item ini.
        """
        x = self.x()
        y = self.y()
        rz = self.rotation()
        
        z = self.pose_z
        rx = self.pose_rx
        ry = self.pose_ry
        
        return x, y, z, rx, ry, rz

    # --- Method-method Anda yang lain tidak berubah ---
        
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
