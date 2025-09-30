"""
grcn_app_state.py - Application state management for the GUI.

Defines:
- AppState enum (IDLE, BUSY, FINISHED)
- AppStateManager to update GUI based on current state
"""

from enum import Enum


class AppState(Enum):
    IDLE = 1
    BUSY = 2
    FINISHED = 3


class AppStateManager:
    """Handles transitions between AppStates and updates the GUI accordingly."""

    def __init__(self, main_window):
        """
        :param main_window: Reference to the QMainWindow (to access control panel + status bar).
        """
        self.main_window = main_window
        self.logger = main_window.logger
        self.state = AppState.IDLE

    def set_state(self, new_state: AppState):
        """Switches the application state and updates UI controls."""
        self.state = new_state
        self.logger.info(f"--- Application state changed to: {self.state.name} ---")

        is_busy = (self.state == AppState.BUSY)

        # Disable object editing while busy
        self.main_window.control_panel.add_object_btn.setDisabled(is_busy)
        self.main_window.control_panel.delete_btn.setDisabled(is_busy)
        self.main_window.control_panel.reset_btn.setDisabled(is_busy)
        self.main_window.control_panel.rotate_clockwise_btn.setDisabled(is_busy)
        self.main_window.control_panel.rotate_counter_clockwise_btn.setDisabled(is_busy)

        # Manage analyze/cancel button states
        if self.state == AppState.IDLE:
            self.main_window.control_panel.analyze_btn.setEnabled(True)
            self.main_window.control_panel.emergency_btn.setEnabled(False)
        elif self.state == AppState.BUSY:
            self.main_window.control_panel.analyze_btn.setEnabled(False)
            self.main_window.control_panel.emergency_btn.setEnabled(True)
        elif self.state == AppState.FINISHED:
            self.main_window.control_panel.analyze_btn.setEnabled(False)
            self.main_window.control_panel.emergency_btn.setEnabled(False)
            self.main_window.control_panel.reset_btn.setEnabled(True)

        # Status bar hint
        self.main_window.statusBar().showMessage(f"State: {self.state.name}")

