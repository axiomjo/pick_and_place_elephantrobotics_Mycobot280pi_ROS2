"""
vision_perspective_transform_node

This module provides functions to perform the perspective transform on the image based on the four points received from the GUI. (like a piece of paper or a robot workspace)
into a top-down, "unslanted" view.

"""

import cv2
import numpy as np


def order_points_for_warp(raw_pts: np.ndarray) -> np.ndarray:
    """Order arbitrary 4 points into (TR, TL, BL, BR) to match internal dst mapping.

    Destination (see warp_perspective) is defined as:
        dst_pts = [ [S,0], [0,0], [0,S], [S,S] ] -> (TR, TL, BL, BR)

    Args:
        raw_pts (np.ndarray): shape (4,2) unordered corner points (x,y).

    Returns:
        np.ndarray: ordered points (4,2) float32 in (TR, TL, BL, BR) order.
    """
    if raw_pts.shape != (4, 2):
        raise ValueError(f"Expected (4,2) array of points, got shape {raw_pts.shape}")
    pts = raw_pts.astype("float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)  # x - y
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tr, tl, bl, br], dtype=np.float32)


def warp_perspective(frame: np.ndarray, ordered_src_pts: np.ndarray, output_size: int = 600) -> np.ndarray:
    """Perform perspective warp given points already ordered as (TR, TL, BL, BR)."""
    dst_pts = np.float32([
        [output_size, 0],   # TR
        [0, 0],             # TL
        [0, output_size],   # BL
        [output_size, output_size]  # BR
    ])
    M = cv2.getPerspectiveTransform(ordered_src_pts, dst_pts)
    return cv2.warpPerspective(frame, M, (output_size, output_size))


def compute_topdown(frame: np.ndarray, raw_pts: np.ndarray, output_size: int = 600) -> np.ndarray:
    """High-level helper: validate, order, then warp.

    Args:
        frame: BGR image
        raw_pts: (4,2) unordered points from GUI
        output_size: side length of output square

    Returns:
        Top-down warped image (np.ndarray)
    """
    ordered = order_points_for_warp(raw_pts)
    return warp_perspective(frame, ordered, output_size=output_size)
