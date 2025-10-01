"""
Defines the JointMonitorWidget, a widget for visualizing robot joint angles that uses the interface JointStates [ ROS builtin]. yes. its not a typo.
This widget creates a series of labels and progress bars to show the state
of each joint in a human-readable format. It is a "dumb" component that
receives data via a public slot.
"""

import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import pyqtSlot

# Type hinting for the slot method
from sensor_msgs.msg import JointState

# Define a safe operating range for the joints in degrees for visualization
JOINT_MIN_DEG = -170
JOINT_MAX_DEG = 170

class JointMonitorWidget(QWidget):
    """A widget that displays multiple joint states with progress bars."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        self.joint_widgets = {}  # Dictionary to store widgets for easy access
        
        # Assume 6 joints and create placeholders initially
        for i in range(1, 7):
            # Use a simple placeholder key that we can reliably access by index
            placeholder_key = f"joint_{i}"
            self._create_joint_display(placeholder_key, f"Joint {i}")

    def _create_joint_display(self, key: str, display_name: str):
        """Helper function to create the widgets for a single joint."""
        name_label = QLabel(f"{display_name}:")
        name_label.setFixedWidth(100)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, JOINT_MAX_DEG - JOINT_MIN_DEG)
        progress_bar.setTextVisible(False)

        value_label = QLabel("0.0°")
        value_label.setFixedWidth(60)

        joint_layout = QHBoxLayout()
        joint_layout.addWidget(name_label)
        joint_layout.addWidget(progress_bar)
        joint_layout.addWidget(value_label)
        self.main_layout.addLayout(joint_layout)

        # Store the widgets that need updating
        self.joint_widgets[key] = {
            'name_label': name_label,
            'bar': progress_bar,
            'value': value_label
        }

    
    def update_joint_display(self, joint_state_msg: JointState):
        """Public slot to update all joint displays from a JointState message."""
        joint_names = joint_state_msg.name
        joint_positions_rad = joint_state_msg.position

        for i in range(len(joint_names)):
            name = joint_names[i]
            position_rad = joint_positions_rad[i]
            
            # Use the index to map to our placeholder widgets
            placeholder_key = f"joint_{i+1}"

            if placeholder_key in self.joint_widgets:
                widgets = self.joint_widgets[placeholder_key]
                position_deg = math.degrees(position_rad)
                
                # Update the name label with the actual name from the message
                widgets['name_label'].setText(f"{name}:")
                
                # Update the numerical value label
                widgets['value'].setText(f"{position_deg:.1f}°")
                
                # Map the degree value to the progress bar's range and update it
                bar_value = int(position_deg - JOINT_MIN_DEG)
                widgets['bar'].setValue(bar_value)
