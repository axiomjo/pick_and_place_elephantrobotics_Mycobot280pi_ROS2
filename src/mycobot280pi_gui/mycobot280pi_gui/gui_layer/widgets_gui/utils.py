"""
gui_utils.py - Common utility functions for the GUI layer.
"""
import cv2
import numpy as np
from PyQt5.QtGui import QPixmap, QImage

def convert_cv_to_pixmap(cv_image: np.ndarray) -> QPixmap:
    """
    Converts an OpenCV image (BGR numpy array) to a QPixmap.
    Returns an empty QPixmap if conversion fails.
    """
    if cv_image is None or cv_image.size == 0:
        return QPixmap()
    try:
        # Convert BGR (OpenCV default) to RGB (Qt default)
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        return QPixmap.fromImage(qt_image)
        
    except (cv2.error, Exception) as e:
        print(f"Error converting CV image to QPixmap: {e}")
        return QPixmap()
