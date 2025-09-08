"""
vodn_message_converter.py

Converts detection results to ManyDetectedObjects ROS message.
"""

from mycobot280pi_interfaces.msg import ManyDetectedObjects, OneDetectedObject, Point2D
from std_msgs.msg import Header

def objects_to_rosmsg(detected_objects, header: Header):
    """
    Converts a list of detected objects to a ManyDetectedObjects ROS message.

    Args:
        detected_objects (List[dict]): List of dicts with keys id, x, y, w, h.
        header (std_msgs.msg.Header): Header from the input image.

    Returns:
        ManyDetectedObjects: ROS message containing all detected objects.
    """
    msg = ManyDetectedObjects()
    msg.header = header
    for obj in detected_objects:
        one = OneDetectedObject()
        one.id = obj['id']
        # Center point calculation
        center = Point2D()
        center.x = float(obj['x'] + obj['w'] // 2)
        center.y = float(obj['y'] + obj['h'] // 2)
        one.center_point = center
        one.width = obj['w']
        one.height =
