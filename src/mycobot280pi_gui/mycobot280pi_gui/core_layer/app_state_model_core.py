"""
app_state_model_core.py - Defines the AppStateModel.

This class is the "source of truth" for the application's high-level state
(e.g., IDLE, BUSY, FINISHED). It holds the current state and emits a signal
whenever that state changes.
"""

from PyQt5.QtCore import QObject, pyqtSignal

# Import the Enum which defines the *type* of state we can be in.
from .state_enum_core import AppState

class AppStateModel(QObject):
    """The Model that holds and manages the application's current state."""

    # This signal is emitted whenever the state changes.
    # Views like the ActionPanelGUI will connect to this to update their buttons.
    state_changed = pyqtSignal(AppState)

    def __init__(self, parent=None):
        """Initializes the AppStateModel with a default state of IDLE."""
        super().__init__(parent)
        
        # This private attribute holds the single, current state value.
        self._state = AppState.IDLE

    # --- Public Method (for Controllers to call) ---

    def set_state(self, new_state): # (new_state: AppState)
        """
        Sets the application's state and emits a signal if it has changed.
        """
        # For efficiency, only update and emit if the state is actually different.
        if self._state == new_state:
            return
            
        self._state = new_state
        self.state_changed.emit(self._state)

    # --- Public Getter Method (for Views/Controllers to query) ---
    
    def get_state(self): 
        """
        Provides safe, read-only access to the current state.
        """
        return self._state
