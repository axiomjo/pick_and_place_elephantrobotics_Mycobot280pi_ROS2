"""
action_panel_gui.py - Defines the ActionPanelGUI widget.

This panel is a View that holds all the main control buttons for managing
the workspace and starting/stopping complex actions. It updates its own button
states by observing the AppStateModel.
"""

from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout
from PyQt5.QtCore import pyqtSlot

# Import the AppState enum to understand the state signals it will receive.
from ...core_layer.state_enum_core import AppState

class ActionPanelGUI(QWidget):
    """A container widget that holds all the main control buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QGridLayout(self)

        # --- Create Button Instances ---
        self.add_object_btn = QPushButton("Add New Objects")
        self.reset_btn = QPushButton("Reset Plane")
        self.analyze_btn = QPushButton("Start Pick & Place")
        self.emergency_btn = QPushButton("Cancel Action")
        self.delete_btn = QPushButton("Delete Selected")
        self.rotate_counter_clockwise_btn = QPushButton("Rotate CCW")
        self.rotate_clockwise_btn = QPushButton("Rotate CW")
        self.add_memory_btn = QPushButton("Add Memory Circle")

        # --- Arrange Buttons in Layout ---
        # Row 0: Primary action buttons
        layout.addWidget(self.analyze_btn, 0, 0, 1, 2) # Span 2 columns
        layout.addWidget(self.emergency_btn, 0, 2)
        layout.addWidget(self.delete_btn, 0, 3)

        # Row 1: Utility and modification buttons
        layout.addWidget(self.reset_btn, 1, 0)
        layout.addWidget(self.add_object_btn, 1, 1)
        layout.addWidget(self.rotate_counter_clockwise_btn, 1, 2)
        layout.addWidget(self.rotate_clockwise_btn, 1, 3)
        layout.addWidget(self.add_memory_btn, 2, 0)

        # Set an initial state for the buttons
        self.update_button_states(AppState.IDLE)

    @pyqtSlot(AppState)
    def update_button_states(self, state):
        """
        Public slot to enable/disable buttons based on the application's state.
        This logic was migrated from the old AppStateManager.
        """
        is_busy = (state == AppState.BUSY)

        # Disable object editing while the robot is busy
        self.add_object_btn.setDisabled(is_busy)
        self.delete_btn.setDisabled(is_busy)
        self.reset_btn.setDisabled(is_busy)
        self.rotate_clockwise_btn.setDisabled(is_busy)
        self.rotate_counter_clockwise_btn.setDisabled(is_busy)
        self.add_memory_btn.setDisabled(is_busy)

        # Manage the main action buttons based on state
        if state == AppState.IDLE:
            self.analyze_btn.setEnabled(True)
            self.emergency_btn.setEnabled(False)
            # Allow reset when idle
            self.reset_btn.setEnabled(True)
        elif state == AppState.BUSY:
            self.analyze_btn.setEnabled(False)
            self.emergency_btn.setEnabled(True)
        elif state == AppState.FINISHED:
            self.analyze_btn.setEnabled(False)
            self.emergency_btn.setEnabled(False)
            # When finished, the only sensible next step is to reset
            self.reset_btn.setEnabled(True)
