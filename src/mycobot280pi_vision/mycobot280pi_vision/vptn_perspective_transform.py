"""
# vptn_perspective_transform.py

This file contains the reusable PerspectiveTransformer class with all the OpenCV logic. It is completely independent of ROS. it transorms an image, based on the four points received from the GUI,
into a top-down, "unslanted" view.

"""

# vptn_perspective_transform.py

import cv2
import numpy as np

class PerspectiveTransformer:
    """
    Handles the perspective transformation of an image using OpenCV.
    """
    def __init__(self, output_width: int = 600, output_height: int = 600):
        """
        Initializes the transformer with a desired output image size.

        Args:
            output_width (int): The width of the warped output image.
            output_height (int): The height of the warped output image.
        """
        self.output_width = output_width
        self.output_height = output_height
        
        # Define the destination points for the top-down view.
        # The order must correspond to the source points: top-left, top-right, bottom-right, bottom-left.
        self.destination_points = np.array([
            [0, 0],
            [self.output_width - 1, 0],
            [self.output_width - 1, self.output_height - 1],
            [0, self.output_height - 1]
        ], dtype=np.float32)

    def transform(self, image: np.ndarray, source_points: np.ndarray) :
        """
        Performs the perspective warp on the input image.

        Args:
            image (np.ndarray): The input image from the camera (OpenCV format).
            source_points (np.ndarray): A NumPy array of shape (4, 2) containing the 
                                        four points selected in the GUI.

        Returns:
            np.ndarray or None: The warped, top-down image, or None if the input is invalid.
        """
        if image is None:
            print("Error: Input image is None.")
            return None
        
        if source_points is None or source_points.shape != (4, 2):
            print("Error: Source points are invalid. Must be a (4, 2) NumPy array.")
            return None

        # Calculate the perspective transform matrix
        matrix = cv2.getPerspectiveTransform(source_points, self.destination_points)
        
        # Apply the perspective warp
        warped_image = cv2.warpPerspective(
            image, 
            matrix, 
            (self.output_width, self.output_height)
        )
        
        return warped_image
