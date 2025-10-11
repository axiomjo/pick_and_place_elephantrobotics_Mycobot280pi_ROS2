"""
workspace_ctrl_core.py - Defines the WorkspaceController.

This controller manages the logic for the interactive workspace. It handles
adding objects based on ROS data, resetting the plane, and deleting selected items.
"""
import cv2
import numpy as np
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

# Import the models and views it will interact with
from ..workspace_model_core import WorkspaceModel
from ...gui_layer.widgets_gui.graphics_gui.draggable_item_gui import DraggableItemGUI

# Import type hints for ROS components
from ...ros_layer.ros_facade_bridge import ROS_Facade_Bridge
from mycobot280pi_interfaces.msg import ManyDetectedObjects, OneDetectedObject


# This function is migrated from the old gui_utils.py
def _create_cutout_pixmap(source_image, obj): 
    """
    Crops a source OpenCV image based on a detected object's bounding box.
    This is a private helper function for this module.
    
    return:
        QPixmap
    """
    w = obj.width
    h = obj.height
    x = int(obj.center_point.x - w / 2.0)
    y = int(obj.center_point.y - h / 2.0)
    
    img_h, img_w, _ = source_image.shape
    if w <= 0 or h <= 0 or x < 0 or y < 0 or (x + w) > img_w or (y + h) > img_h:
        return QPixmap()

    cutout_cv = source_image[y:y+h, x:x+w]
    if cutout_cv.size == 0:
        return QPixmap()

    try:
        rgb_cutout = cv2.cvtColor(cutout_cv, cv2.COLOR_BGR2RGB)
        h2, w2, ch = rgb_cutout.shape
        bytes_per_line = ch * w2
        qt_img = QImage(rgb_cutout.data, w2, h2, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qt_img)
    except cv2.error:
        return QPixmap()


class WorkspaceController(QObject):
    """Manages the business logic of the workspace."""

    # Signal to send status updates to the GUI
    status_message_changed = pyqtSignal(str)

    def __init__(self, model, ros_comm, parent=None):
        # (model: WorkspaceModel, ros_comm: ROS_Facade_Bridge, parent: QObject)
        super().__init__(parent)
        
        # --- Dependencies (Injected) ---
        self.model = model
        self.ros_comm = ros_comm
        self.logger = self.ros_comm.get_logger()

        # --- Internal State ---
        # This controller caches the latest ROS data it needs to perform its job.
        self.latest_objects_msg = None
        self.latest_annotated_image = None
    
    # --- Public Slots (for ROS Facade signals) ---

    @pyqtSlot(ManyDetectedObjects)
    def cache_detected_objects(self, objects_msg):
        """Caches the latest detected objects message from the ROS Facade."""
        self.latest_objects_msg = objects_msg

    @pyqtSlot(np.ndarray)
    def cache_annotated_image(self, cv_image):
        """Caches the latest annotated image from the ROS Facade."""
        self.latest_annotated_image = cv_image

    # --- Public Slots (for GUI View signals) ---
    
    @pyqtSlot()
    def reset_plane(self):
        """
        Handles the logic for the "Reset Plane" button.
        Commands the model to clear all its items.
        """
        self.logger.info("Resetting the workspace plane...")
        self.model.clear_all_items()
        self.status_message_changed.emit("Plane has been reset. Ready for new plan.")

    @pyqtSlot(list)
    def delete_selected(self, selected_items):
        """
        Handles the logic for the "Delete Selected" button.
        Commands the model to remove the specified items.
        """
        if not selected_items:
            self.status_message_changed.emit("No items selected to delete.")
            return

        self.logger.info("Deleting {} selected items...".format(len(selected_items)))
        self.model.remove_items(selected_items)
        self.status_message_changed.emit("Deleted {} item(s).".format(len(selected_items)))

    @pyqtSlot()
    def add_new_objects_from_cutouts(self):
        """
        Handles the "Add New Objects" button. Creates DraggableItemGUI instances
        from cached ROS data and commands the model to add them.
        """
        if self.latest_objects_msg is None or self.latest_annotated_image is None:
            self.logger.warn("Add objects called, but ROS data is not ready yet.")
            self.status_message_changed.emit("ROS data is not available to add objects.")
            return

        self.logger.info("Processing detected objects to add to the workspace.")
        newly_created_items = []
        image_to_process = self.latest_annotated_image
        
        for obj in self.latest_objects_msg.objects:
            try:
                pixmap = _create_cutout_pixmap(image_to_process, obj)
                if pixmap.isNull():
                    continue

                # The QGraphicsScene will be inverted, so we flip the pixmap vertically now.
                transform = QTransform()
                transform.scale(1, -1)
                flipped_pixmap = pixmap.transformed(transform)
                if flipped_pixmap.isNull():
                    continue
                
                # Create the GUI item but DON'T add it to a scene here.
                item = DraggableItemGUI(pixmap=flipped_pixmap, detected_object=obj)
                newly_created_items.append(item)

            except Exception as e:
                self.logger.error("Error processing object ID {}: {}".format(obj.id, e), exc_info=True)
        
        # Command the model to add all the newly created items in one go.
        self.model.add_items(newly_created_items)
        self.status_message_changed.emit("Added {} new objects to the plane.".format(len(newly_created_items)))
