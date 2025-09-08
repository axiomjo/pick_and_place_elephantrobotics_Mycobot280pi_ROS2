"""
grcn_pyqt_widget.py

A custom PyQt5 widget for displaying images (e.g., camera feed, corrected image)
with optional overlays such as bounding boxes for detected objects.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPixmap, QPen, QColor
from PyQt5.QtCore import Qt, QRect



from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt

class DraggableObjectItem(QGraphicsRectItem):
    def __init__(self, x, y, w, h, object_id=None, color=QColor(0, 255, 0, 120)):
        super().__init__(x, y, w, h)
        self.setBrush(QBrush(color))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)
        self.object_id = object_id
        self.width = w
        self.height = h

    def mouseReleaseEvent(self, event):
        # You can emit a signal or call a callback here to notify the GUI of the new position
        super().mouseReleaseEvent(event)
        
            
        
        
class ImageDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.bounding_boxes = []  # List of (x, y, w, h)
        self.box_color = QColor(0, 255, 0)
        self.setMinimumSize(320, 240)

    def set_image(self, qimage):
        """Set the image to display (as QImage or QPixmap)."""
        if isinstance(qimage, QPixmap):
            self.pixmap = qimage
        else:
            self.pixmap = QPixmap.fromImage(qimage)
        self.update()

    def set_bounding_boxes(self, boxes):
        """
        Set bounding boxes to overlay.
        boxes: list of (x, y, w, h)
        """
        self.bounding_boxes = boxes
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            scaled_pixmap = self.pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled_pixmap)
            # Calculate scaling ratio for overlay
            x_ratio = scaled_pixmap.width() / self.pixmap.width()
            y_ratio = scaled_pixmap.height() / self.pixmap.height()
            for box in self.bounding_boxes:
                x, y, w, h = box
                pen = QPen(self.box_color, 2)
                painter.setPen(pen)
                rect = QRect(
                    int(x * x_ratio),
                    int(y * y_ratio),
                    int(w * x_ratio),
                    int(h * y_ratio)
