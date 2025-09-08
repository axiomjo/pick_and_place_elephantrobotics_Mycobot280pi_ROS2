from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QPainter, QPen, QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint

# --- Perspective Editor Dialog ---
class PerspectiveEditorDialog(QDialog):
    def __init__(self, parent=None, image=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Perspective Points")
        self.setModal(True)
        self.image = image  # QImage or QPixmap
        self.points = []  # List of QPoint
        self.resize(640, 480)

        layout = QVBoxLayout(self)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.instruction_label = QLabel("Click 4 points (in order: top-left, top-right, bottom-right, bottom-left)")
        layout.addWidget(self.instruction_label)

        self.confirm_btn = QPushButton("Confirm & Send")
        self.confirm_btn.clicked.connect(self.on_confirm)
        self.confirm_btn.setEnabled(False)
        layout.addWidget(self.confirm_btn)

        self.update_image()
        self.image_label.mousePressEvent = self.on_image_click

    def update_image(self):
        if self.image is None:
            self.image_label.setText("No image available.")
            return
        # Draw points on a copy of the image
        if isinstance(self.image, QPixmap):
            pixmap = self.image.copy()
        else:
            pixmap = QPixmap.fromImage(self.image)
        painter = QPainter(pixmap)
        pen = QPen(Qt.red, 8)
        painter.setPen(pen)
        for idx, pt in enumerate(self.points):
            painter.drawPoint(pt)
            painter.drawText(pt + QPoint(5, -5), str(idx+1))
        painter.end()
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_image_click(self, event):
        if self.image is None or len(self.points) >= 4:
            return
        label_size = self.image_label.size()
        pixmap = self.image_label.pixmap()
        if pixmap is None:
            return
        # Map click position to image coordinates
        x = event.pos().x()
        y = event.pos().y()
        pixmap_w = pixmap.width()
        pixmap_h = pixmap.height()
        label_w = label_size.width()
        label_h = label_size.height()
        # Centered scaling
        x_offset = (label_w - pixmap_w) // 2
        y_offset = (label_h - pixmap_h) // 2
        img_x = x - x_offset
        img_y = y - y_offset
        if 0 <= img_x < pixmap_w and 0 <= img_y < pixmap_h:
            # Map to original image size
            orig_w = self.image.width() if isinstance(self.image, QImage) else self.image.size().width()
            orig_h = self.image.height() if isinstance(self.image, QImage) else self.image.size().height()
            scale_x = orig_w / pixmap_w
            scale_y = orig_h / pixmap_h
            pt = QPoint(int(img_x * scale_x), int(img_y * scale_y))
            self.points.append(pt)
            self.update_image()
            if len(self.points) == 4:
                self.confirm_btn.setEnabled(True)

    def on_confirm(self):
        if len(self.points) != 4:
            QMessageBox.warning(self, "Not enough points", "Please select 4 points.")
            return
        self.accept()

    def get_points(self):
        # Return as list of (x, y)
        return [(pt.x(), pt.y()) for pt in self.points]
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
                )
                painter.drawRect(rect)
