"""
workspace_model_core.py - Defines the WorkspaceModel.

This class is the "source of truth" for the state of the interactive workspace.
It holds the list of all draggable items on the plane and emits signals when
this list is modified.
"""

from PyQt5.QtCore import QObject, pyqtSignal
from typing import List

# We import the DraggableItemGUI, as this model's job is to manage a list of them.
from ..gui_layer.widgets_gui.graphics_gui.draggable_item_gui import DraggableItemGUI

class WorkspaceModel(QObject):
    """The Model that holds and manages the state of the workspace items."""
    
    # This signal is emitted whenever the list of items changes.
    # The View will connect to this to know when to redraw itself.
    items_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initializes the WorkspaceModel."""
        super().__init__(parent)
        
        # This private attribute is the core data. No one outside this class
        # should ever touch this list directly, enforcing encapsulation.
        self._items_on_plane: List[DraggableItemGUI] = []

    # --- Public Methods (for the Controller to call) ---
    
    def add_items(self, new_items: List[DraggableItemGUI]):
        """
        Adds a list of new items to the workspace and emits a signal.
        """
        self._items_on_plane.extend(new_items)
        self.items_changed.emit()

    def remove_items(self, items_to_remove: List[DraggableItemGUI]):
        """
        Removes a list of specific items from the workspace and emits a signal.
        """
        # Ensure we only emit the signal once for efficiency
        items_were_removed = False
        for item in items_to_remove:
            if item in self._items_on_plane:
                self._items_on_plane.remove(item)
                items_were_removed = True
        
        if items_were_removed:
            self.items_changed.emit()

    def clear_all_items(self):
        """
        Removes all items from the workspace and emits a signal.
        """
        if not self._items_on_plane:
            return # Nothing to do, so don't emit a signal.
            
        self._items_on_plane.clear()
        self.items_changed.emit()

    # --- Public Getter Method (for the View to call) ---
        
    def get_all_items(self):
        """
        Provides safe, read-only access to the list of items. The View will
        call this to get the items it needs to draw.
        """
        return self._items_on_plane
