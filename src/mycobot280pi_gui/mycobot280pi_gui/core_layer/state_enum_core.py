"""
state_enum_core.py - Defines the core application state enumeration.
"""

from enum import Enum

class AppState(Enum):
    """Enumeration for the application's high-level state."""
    IDLE = 1      # Ready for user input or a new plan
    BUSY = 2      # A complex action is currently running
    FINISHED = 3  # The complex action has completed (success or fail)
