#!/usr/bin/env python3

"""
Defines the ControlPanel, a dedicated widget for the main action buttons.

This widget's sole responsibility is to create and lay out the primary buttons
used for robot interaction (e.g., Start, Cancel, Reset). It is a passive
component; all functionality is connected by the MainWindow.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton

class ControlPanel(QWidget):
    """A container widget that holds all the main control buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout for this widget
        layout = QHBoxLayout(self)

        # Create all the button instances
        self.send_btn = QPushButton("Send to Robot")
        self.add_object_btn = QPushButton("Add New Objects")
        self.reset_btn = QPushButton("Reset Plane")
        self.analyze_btn = QPushButton("Start Pick & Place")
        self.emergency_btn = QPushButton("Cancel Action")
        self.delete_btn = QPushButton("Delete Selected")
        self.rotate_counter_clockwise_btn = QPushButton("Rotate CCW")
        self.rotate_clockwise_btn = QPushButton("Rotate CW")
        
        # Disable buttons that should only be enabled by the state machine
        self.send_btn.setDisabled(True) 
        self.emergency_btn.setEnabled(False)

        # Add buttons to the layout in a logical order
        layout.addWidget(self.analyze_btn)
        layout.addWidget(self.emergency_btn)
        layout.addWidget(self.delete_btn)
        layout.addStretch() # Adds a flexible space
        layout.addWidget(self.reset_btn)
        layout.addWidget(self.add_object_btn)
        layout.addWidget(self.rotate_counter_clockwise_btn)
        layout.addWidget(self.rotate_clockwise_btn)
        layout.addStretch() # Adds another flexible space
        layout.addWidget(self.send_btn)
