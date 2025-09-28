"""
todo: tambahin doscsting
"""
import cv2
from PyQt5.QtGui import QImage, QPixmap
from mycobot280pi_interfaces.msg import OneDetectedObject


from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsPixmapItem, QGraphicsItem, QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import  QColor, QPainter, QPen, QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint

# ----------- Helper Classes ----------------------
class PointHandle(QGraphicsEllipseItem):
    def __init__(self, x, y, radius=8, color=QColor("red")):
        super().__init__(-radius/2, -radius/2, radius, radius)
        self.setBrush(color)
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsScenePositionChanges, True)
        self.setPos(x, y)

    def get_point(self):
        return int(self.pos().x()), int(self.pos().y())


class DraggableItem(QGraphicsPixmapItem):
    """ A QGraphicsPixmapItem that can be moved and rotated. """
    def __init__(self, pixmap, object_id, parent=None):
        super().__init__(pixmap, parent)
        
        self.object_id = object_id
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable
        )
        # Set transform origin to the center of the pixmap
        self.setTransformOriginPoint(self.boundingRect().center())
        
    def mouseReleaseEvent(self, event):
        
        final_true_pos = self.mapToScene(self.boundingRect().center())
        print(f"Item CENTERPOINT released at: ({final_true_pos.x():.1f}, {final_true_pos.y():.1f}), "
              f"rotation={self.rotation():.1f}")
        super().mouseReleaseEvent(event)



# ----------- Helper Function ----------------------
def create_cutout_pixmap(source_image, obj: OneDetectedObject) -> QPixmap:
    """
    This is our "master blueprint" for creating a cutout.
    It takes the full image and one object's data, performs the crop,
    and returns a ready-to-display QPixmap.
    """
    # 1. Reconstruct the bounding box from the message fields
    w = obj.width
    h = obj.height
    x = int(obj.center_point.x - w / 2.0)
    y = int(obj.center_point.y - h / 2.0)
    
    if w <= 0 or h <= 0:
        return QPixmap() # Return an empty pixmap if the box is invalid

    # 2. Crop the image using the calculated box
    cutout_cv = source_image[y:y+h, x:x+w]
    
    # 3. Convert the OpenCV image (BGR) to a QPixmap (RGB)
    rgb_cutout = cv2.cvtColor(cutout_cv, cv2.COLOR_BGR2RGB)
    h2, w2, ch = rgb_cutout.shape
    qt_img = QImage(rgb_cutout.data, w2, h2, ch*w2, QImage.Format_RGB888)
    
    return QPixmap.fromImage(qt_img)
