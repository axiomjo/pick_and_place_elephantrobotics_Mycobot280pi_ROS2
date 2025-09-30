
"""
General purpose utility functions for the GUI package.

This file contains helper functions that can be used by various GUI components
but do not belong to any single widget class.
"""

import cv2
from PyQt5.QtGui import QImage, QPixmap
from mycobot280pi_interfaces.msg import OneDetectedObject
import numpy as np


def create_cutout_pixmap(source_image: np.ndarray, obj: OneDetectedObject) -> QPixmap:
    """
    Crops a source OpenCV image based on a detected object's bounding box data.

    Args:
        source_image: The full OpenCV image (in BGR format).
        obj: A OneDetectedObject ROS message containing the object's metadata.

    Returns:
        A QPixmap of the cropped object, ready for display in Qt. Returns an
        empty QPixmap if the bounding box is invalid.
    """
    # 1. Reconstruct the bounding box from the message fields
    w = obj.width
    h = obj.height
    x = int(obj.center_point.x - w / 2.0)
    y = int(obj.center_point.y - h / 2.0)
    
    # 2. Add boundary checks for robustness
    img_h, img_w, _ = source_image.shape
    if w <= 0 or h <= 0 or x < 0 or y < 0 or (x + w) > img_w or (y + h) > img_h:
        # Return an empty pixmap if the box is invalid or out of bounds
        return QPixmap()

    # 3. Crop the image using the calculated box
    cutout_cv = source_image[y:y+h, x:x+w]
    
    if cutout_cv.size == 0:
        return QPixmap() # Return empty pixmap if crop result is empty

    # 4. Convert the OpenCV image (BGR) to a QPixmap (RGB)
    try:
        rgb_cutout = cv2.cvtColor(cutout_cv, cv2.COLOR_BGR2RGB)
        h2, w2, ch = rgb_cutout.shape
        bytes_per_line = ch * w2
        qt_img = QImage(rgb_cutout.data, w2, h2, bytes_per_line, QImage.Format_RGB888)
        
        return QPixmap.fromImage(qt_img)
    except cv2.error:
        # Handle potential errors during color conversion if the cutout is malformed
        return QPixmap()
