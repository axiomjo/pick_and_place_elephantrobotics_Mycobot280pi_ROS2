"""
workspace_ctrl_core.py - Defines the WorkspaceController.

This controller manages the logic for the interactive workspace. It handles
adding objects based on ROS data, resetting the plane, and deleting selected items.
"""
import cv2
import numpy as np
import traceback
from copy import deepcopy

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QRectF, Qt
from PyQt5.QtGui import QImage, QPixmap, QTransform, QPainter, QColor, QBrush, QFont

from ..workspace_model_core import WorkspaceModel
from ...gui_layer.widgets_gui.graphics_gui.draggable_item_gui import DraggableItemGUI
from ...ros_layer.ros_facade_bridge import ROS_Facade_Bridge
from mycobot280pi_interfaces.msg import ManyDetectedObjects, OneDetectedObject, Point2D
from ...gui_layer.widgets_gui.gui_utils import convert_cv_to_pixmap

def _create_cutout_pixmap(source_image, obj): # (np.ndarray, OneDetectedObject) -> QPixmap
    w, h = obj.width, obj.height
    x, y = int(obj.center_point.x - w / 2.0), int(obj.center_point.y - h / 2.0)
    img_h, img_w, _ = source_image.shape
    if w <= 0 or h <= 0 or x < 0 or y < 0 or (x + w) > img_w or (y + h) > img_h:
        return QPixmap()
    cutout_cv = source_image[y:y+h, x:x+w]
    if cutout_cv.size == 0: return QPixmap()
    try:
        rgb_cutout = cv2.cvtColor(cutout_cv, cv2.COLOR_BGR2RGB)
        h2, w2, ch = rgb_cutout.shape
        bytes_per_line = ch * w2
        qt_img = QImage(rgb_cutout.data, w2, h2, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qt_img)
    except cv2.error:
        return QPixmap()

def _create_circle_pixmap(size: int, color: QColor, text: str)
    """Creates a circular QPixmap with text centered on it."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    painter.setBrush(QBrush(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    
    font = QFont()
    font.setPixelSize(int(size * 0.6))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("white")) # White text
    
    text_rect = QRectF(0, 0, size, size)
    painter.drawText(text_rect, Qt.AlignCenter, text)
    painter.end()
    
    return pixmap




class WorkspaceController(QObject):
    status_message_changed = pyqtSignal(str)

    def __init__(self, model, ros_comm, parent=None):
        super().__init__(parent)
        self.model = model
        self.ros_comm = ros_comm
        self.logger = self.ros_comm.get_logger()
        self.latest_objects_msg = None
        self.latest_annotated_image = None
        self._current_selection = []
        self._memory_item_counter = 0 # To give unique IDs
        

    @pyqtSlot(ManyDetectedObjects)
    def cache_detected_objects(self, objects_msg):
        self.latest_objects_msg = objects_msg

    @pyqtSlot(np.ndarray)
    def cache_annotated_image(self, cv_image):
        """
        Slot to receive the annotated image from the ROS facade.
        """
        self.latest_annotated_image = cv_image
        bg_pixmap = convert_cv_to_pixmap(cv_image)
        if self.model and not bg_pixmap.isNull():
            self.model.set_background_pixmap(bg_pixmap)

    @pyqtSlot(list)
    def cache_current_selection(self, selected_items):
        self._current_selection = selected_items
       
    @pyqtSlot()
    def reset_plane(self):
        self.logger.info("Resetting the workspace plane...")
        self.model.clear_all_items()
        self._memory_item_counter = 0
        self.status_message_changed.emit("Plane has been reset. Ready for new plan.")
        
        

    @pyqtSlot()
    def delete_selected(self):
        if not self._current_selection:
            self.status_message_changed.emit("No items selected to delete.")
            return
        items_to_delete = self._current_selection
        self.logger.info("Deleting {} selected items...".format(len(items_to_delete)))
        self.model.remove_items(items_to_delete)
        self.status_message_changed.emit("Deleted {} item(s).".format(len(items_to_delete)))
        self._current_selection = []


    @pyqtSlot()
    def add_memory_circle(self):
    """
        Creates a new, manually-added DraggableItemGUI and adds it to the model.
        """
        
        try:
            CIRCLE_SIZE = 25 # Pixels (made slightly larger for text)
            item_id_str = str(self._memory_item_counter)
            dummy_obj = OneDetectedObject()
            dummy_obj.id = f"memory_{item_id_str}"
            dummy_obj.center_point = Point2D(x=0.0, y=0.0)
            dummy_obj.width = CIRCLE_SIZE
            dummy_obj.height = CIRCLE_SIZE
            
            base_color = QColor("#3498db")
            base_hue = base_color.hue()
            hue_shift = (self._memory_item_counter * 37) % 360
            new_hue = (base_hue + hue_shift) % 360
            new_color = QColor.fromHsv(new_hue, base_color.saturation(), base_color.value())
            
            pixmap = _create_circle_pixmap(CIRCLE_SIZE, new_color, item_id_str)
            
            transform = QTransform() 
            transform.scale(1, -1)
            flipped_pixmap = pixmap.transformed(transform)
            
            item = DraggableItemGUI(pixmap=flipped_pixmap, detected_object=dummy_obj)
            self.model.add_items([item])
            self.status_message_changed.emit(f"Added new memory item: {dummy_obj.id}")
            self._memory_item_counter += 1
            
        except Exception as e:
            self.logger.error(f"Failed to add memory circle: {e}")
            self.status_message_changed.emit("Error adding memory item.")
        
    
    @pyqtSlot()
    def add_new_objects_from_cutouts(self):
        """
        Creates items for ALL currently detected objects and adds them to the model.
        The coordinate transformation from image space to scene space is done here.
        """
        if self.latest_objects_msg is None or self.latest_annotated_image is None:
            self.logger.warn("Add objects called, but ROS data is not ready yet.")
            self.status_message_changed.emit("ROS data is not available to add objects.")
            return

        newly_created_items = []
        image_to_process = self.latest_annotated_image
        img_h, img_w, _ = image_to_process.shape
        cam_center_x = img_w / 2.0
        cam_center_y = img_h / 2.0

        for obj in self.latest_objects_msg.objects:
            try:
                # --- Perform coordinate transformation FIRST ---
                scene_x = obj.center_point.x - cam_center_x
                scene_y = -(obj.center_point.y - cam_center_y) # Invert Y for scene

                # --- Create a corrected data object ---
                # This ensures the item's internal data matches the scene.
                corrected_obj = deepcopy(obj)
                corrected_obj.center_point.x = scene_x
                corrected_obj.center_point.y = scene_y
                
                # Create the pixmap from the original image and original object data
                pixmap = _create_cutout_pixmap(image_to_process, obj)
                if pixmap.isNull(): continue

                # Flip the pixmap visually to match the scene's inverted Y-axis
                transform = QTransform(); transform.scale(1, -1)
                flipped_pixmap = pixmap.transformed(transform)
                if flipped_pixmap.isNull(): continue
                
                # --- Pass the CORRECTED object to the constructor ---
                item = DraggableItemGUI(pixmap=flipped_pixmap, detected_object=corrected_obj)
                
                # The item's __init__ will now handle setting the correct position.
                # The manual setPos call is no longer needed here.
                
                newly_created_items.append(item)

            except Exception as e:
                error_msg = "Error processing object ID {}: {}".format(obj.id, e)
                traceback_str = traceback.format_exc()
                self.logger.error(f"{error_msg}\n---\n{traceback_str}\n---")
        
        if newly_created_items:
            self.model.add_items(newly_created_items)
            self.status_message_changed.emit("Added {} new objects to the plane.".format(len(newly_created_items)))
        else:
            self.status_message_changed.emit("No objects were detected to add.")
