"""
vodn_object_detection.py

Contains the vision algorithm for detecting objects in an image.
"""

import cv2
import numpy as np

def detect_objects(frame):
    """
    Detects objects in the input image using simple image processing.

    Args:
        frame (np.ndarray): The input image (BGR).

    Returns:
        List[dict]: List of detected objects, each as a dict with keys: x, y, w, h.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected_objects = []
    obj_id = 0
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Filter out small noise
        if w < 20 or h < 20:
            continue
        detected_objects.append({
            'id': obj_id,
            'x': x,
            'y': y,
            'w': w,
            'h': h
        })
        obj_id += 1

    return detected_objects
