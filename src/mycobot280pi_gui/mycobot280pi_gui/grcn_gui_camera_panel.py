"""
grcn_gui_camera_panel.py

PyQt5 panel for displaying the undistorted camera image and editing the four perspective points.
Subscribes to `/vision/msg_undistorted_image` and publishes `/gui/msg_four_perspective_points`.
"""

import sys
from PyQt5.QtWidgets import QWidget, QLabel, QApplication
from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtCore import Qt, QPointF, pyqtSignal

class CameraPanel(QWidget):
    def __init__(self, ros_comm=None, parent=None):
        super().__init__(parent)
        self.ros_comm = ros_comm
        self.image = None
        self.points = [QPointF(100, 100), QPointF(400, 100), QPointF(400, 400), QPointF(100, 400)]
        self.drag_index = None
        self.setMinimumSize(600, 600)
        self.setMouseTracking(True)
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 600, 600)
        self.label.show()
        if self.ros_comm:
            # connect to new unified signal naming
            self.ros_comm.undistorted_image_received.connect(self.set_image)

    def set_image(self, cv_image):
        # cv_image: numpy array (BGR)
        height, width, _ = cv_image.shape
        bytes_per_line = 3 * width
        qimg = QImage(cv_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.image = qimg.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        self.update()

    def update_points_from_ros(self, points):
        # points: list of (x, y)
        self.points = [QPointF(x, y) for x, y in points]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.image:
            painter.drawImage(0, 0, self.image)
        # Draw points and lines
        painter.setPen(QColor(0, 255, 0))
        for i, pt in enumerate(self.points):
            painter.setBrush(QColor(255, 0, 0))
            painter.drawEllipse(pt, 8, 8)
            painter.setPen(QColor(0, 255, 0))
            painter.drawText(pt.x() + 10, pt.y() - 10, f"{i+1}")
        # Draw lines between points
        painter.setPen(QColor(0, 255, 0))
        for i in range(4):
            painter.drawLine(self.points[i], self.points[(i+1)%4])

    def mousePressEvent(self, event):
        for i, pt in enumerate(self.points):
            if (pt - event.pos()).manhattanLength() < 15:
                self.drag_index = i
                break

    def mouseMoveEvent(self, event):
        if self.drag_index is not None:
            self.points[self.drag_index] = event.pos()
            self.update()
            self.publish_points()

    def mouseReleaseEvent(self, event):
        self.drag_index = None

    def publish_points(self):
        if self.ros_comm:
            pts = [(pt.x(), pt.y()) for pt in self.points]
            self.ros_comm.publish_four_points(pts)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    panel = CameraPanel()
    panel.show()
    sys.exit(app.exec_())
