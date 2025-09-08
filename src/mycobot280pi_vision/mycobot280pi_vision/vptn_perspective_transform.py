"""
vision_perspective_transform.py

This module provides functions to detect corners in an image and perform a perspective transform,
turning a slanted or angled view of a rectangle (like a piece of paper or a robot workspace)
into a top-down, "unwarped" view.

[8 Sep 2025]
"""

import cv2
import numpy as np

def detect_quadrilateral_corners(frame):
    """
    Detects the largest quadrilateral (4-sided shape) in the image.
    Returns its corner points if found, otherwise None.

    Args:
        frame (np.ndarray): The input image.

    Returns:
        np.ndarray or None: Array of 4 corner points, or None if not found.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    quadrilateral_contour = None
    max_area = 0

    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        area = cv2.contourArea(approx)
        if len(approx) == 4 and area > max_area:
            quadrilateral_contour = approx
            max_area = area

    if quadrilateral_contour is None:
        return None

    src_pts = np.float32([pt[0] for pt in quadrilateral_contour])
    return src_pts

def warp_perspective(frame, src_pts, output_size=600):
    """
    Applies a perspective transform to the image using the given source points.

    Args:
        frame (np.ndarray): The input image.
        src_pts (np.ndarray): 4 source points (corners of the quadrilateral).
        output_size (int): The size of the output square image.

    Returns:
        np.ndarray: The warped (top-down) image.
    """
    dst_pts = np.float32([
        [output_size, 0],
        [0, 0],
        [0, output_size],
        [output_size, output_size]
    ])
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(frame, M, (output_size, output_size))
    return warped
