"""
todo: tambahin doscsting
"""


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
    def __init__(self, pixmap, parent=None):
        super().__init__(pixmap, parent)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable
        )
        # Set transform origin to the center of the pixmap
        self.setTransformOriginPoint(self.boundingRect().center())
        
    def mouseReleaseEvent(self, event):
        final_local_pos = self.scenePos()
        print(f"LOCALLY, Item released at: ({final_local_pos.x():.1f}, {final_local_pos.y():.1f}), "
              f"rotation={self.rotation():.1f}")
              
        final_true_pos = self.mapToScene(self.boundingRect().center())
        print(f"Item released at: ({final_true_pos.x():.1f}, {final_true_pos.y():.1f}), "
              f"rotation={self.rotation():.1f}")
        super().mouseReleaseEvent(event)

