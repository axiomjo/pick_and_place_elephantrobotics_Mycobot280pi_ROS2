"""
grcn_plane_manager.py - Handles working plane operations for the GUI.
"""

from PyQt5.QtGui import QTransform

from .utils import create_cutout_pixmap
from .widgets.components.graphics.grcn_draggable_item import DraggableItem
from .grcn_app_state import AppState


class PlaneManager:
    """Manages the working plane contents and object placement."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = main_window.logger

    def reset_plane(self):
        """Clears the working plane and sets state back to IDLE."""
        self.main_window.working_plane.reset_scene()
        self.main_window.app_state_mgr.set_state(AppState.IDLE)
        self.main_window.statusBar().showMessage("Plane has been reset. Ready for new plan.")

    def add_new_objects_from_cutouts(self):
        """Adds new draggable items from the latest cached ROS image + objects."""
        if self.main_window.app_state_mgr.state != AppState.IDLE:
            self.main_window.statusBar().showMessage(
                "Cannot add objects while an action is running or finished.", 3000
            )
            return

        if (
            self.main_window.latest_objects_msg is None
            or self.main_window.latest_annotated_image is None
        ):
            self.logger.warn("Add objects called, but data is not ready yet.")
            self.main_window.statusBar().showMessage("Data not available to add objects.")
            return

        image_to_process = self.main_window.latest_annotated_image
        img_height, img_width, _ = image_to_process.shape
        cam_center_x = img_width / 2.0
        cam_center_y = img_height / 2.0

        current_object_count = len(self.main_window.working_plane.items_on_plane)

        for obj in self.main_window.latest_objects_msg.objects:
            try:
                pixmap = create_cutout_pixmap(image_to_process, obj)
                if pixmap.isNull():
                    continue

                transform = QTransform()
                transform.scale(1, -1)
                flipped_pixmap = pixmap.transformed(transform)
                if flipped_pixmap.isNull():
                    continue

                item = DraggableItem(pixmap=flipped_pixmap, detected_object=obj)

                scene_x = obj.center_point.x - cam_center_x
                scene_y = -(obj.center_point.y - cam_center_y)

                final_x = scene_x - (flipped_pixmap.width() / 2)
                final_y = scene_y - (flipped_pixmap.height() / 2)

                item.setPos(final_x, final_y)
                self.main_window.working_plane.working_plane_scene.addItem(item)
                self.main_window.working_plane.items_on_plane.append(item)

            except Exception as e:
                self.logger.error(f"Error processing object ID {obj.id}: {e}", exc_info=True)
                self.main_window.statusBar().showMessage(
                    f"Error processing object ID {obj.id}. See logs.", 5000
                )

        new_items_count = len(self.main_window.working_plane.items_on_plane) - current_object_count
        self.main_window.statusBar().showMessage(f"Added {new_items_count} new objects to the plane.")

    def delete_selected(self):
        """Removes selected draggable items from the working plane."""
        selected_items = self.main_window.working_plane.working_plane_scene.selectedItems()

        for item in selected_items:
            self.main_window.working_plane.working_plane_scene.removeItem(item)
            if item in self.main_window.working_plane.items_on_plane:
                self.main_window.working_plane.items_on_plane.remove(item)

        if selected_items:
            self.main_window.statusBar().showMessage(f"Deleted {len(selected_items)} item(s).")
        else:
            self.main_window.statusBar().showMessage("No items selected to delete.")

