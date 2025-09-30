"""
grcn_selection_manager.py - Handles selection events in the working plane.

This module updates the GUI (status bar + dock panel) whenever a user
selects or deselects items in the working plane.
"""

from .widgets.grcn_draggable_item import DraggableItem


class SelectionManager:
    """Manages GUI updates based on selected items in the working plane."""

    def __init__(self, main_window):
        """
        :param main_window: Reference to the QMainWindow (for access to status bar, dock panel, working plane).
        """
        self.main_window = main_window
        self.logger = main_window.logger

    # -------------------------------------------------------------------------
    # Selection Handling
    # -------------------------------------------------------------------------

    def update_status_bar_with_selection(self):
        """Updates the status bar and dock panel when the selection changes."""
        selected_items = self.main_window.working_plane.working_plane_scene.selectedItems()

        if not selected_items:
            self.main_window.statusBar().showMessage("No item selected.")
            self.main_window.dock_panel.update_rotation_widgets(is_item_selected=False)
            return

        item = selected_items[0]
        if isinstance(item, DraggableItem):
            pos = item.mapToScene(item.boundingRect().center())
            rot = item.rotation()
            message = (
                f"Selected ID: {item.object_id} | "
                f"Pos: ({pos.x():.1f}, {pos.y():.1f}) | "
                f"Rot: {rot:.1f}°"
            )
            self.main_window.statusBar().showMessage(message)
            self.main_window.dock_panel.update_rotation_widgets(
                is_item_selected=True,
                rotation_value=rot
            )

