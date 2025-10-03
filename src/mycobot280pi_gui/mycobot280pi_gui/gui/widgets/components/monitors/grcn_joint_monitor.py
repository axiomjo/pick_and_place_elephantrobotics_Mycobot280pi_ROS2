"""
Defines the JointMonitorWidget, a widget for visualizing robot joint angles that uses the interface JointAnglesArray. 
This widget creates a series of labels and progress bars to show the state
of each joint in a human-readable format. It is a "dumb" component that
receives data via a public slot.
"""

import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import pyqtSlot

from mycobot280pi_interfaces.msg import JointAnglesArray


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

    
    def update_joint_display(self, joint_angle_msg: JointAnglesArray):
        """Public slot to update all joint displays from a JointAnglesArray message."""
        # 1. Extract the list of 6 angles (in degrees, as per your publisher's description)
        latest_angles = joint_angle_msg.joint_angles
        
        # Define default names (matching the initialization)
        # You can replace this list with the actual joint names if you know them.
        default_joint_names = [f"Joint {i}" for i in range(1, 7)]

        # 2. Iterate through the angles using index (i) and value (angle_deg)
        # We only iterate up to the number of angles received OR the number of widgets
        num_joints = min(len(latest_angles), 6) # Assume max 6 joints

        for i in range(num_joints):
            angle_deg = latest_angles[i]
            
            # Map the 0-based index to the 1-based placeholder key (joint_1, joint_2, etc.)
            placeholder_key = f"joint_{i + 1}"

            if placeholder_key in self.joint_widgets:
                widgets = self.joint_widgets[placeholder_key]
                
                # Update the name label (optional, but good if the publisher only sends data)
                widgets['name_label'].setText(f"{default_joint_names[i]}:")
                
                # Update the numerical value label
                widgets['value'].setText(f"{angle_deg:.1f}°")
                
                # Map the degree value to the progress bar's range and update it
                # The bar value must be adjusted by the minimum joint limit (e.g., -170)
                bar_value = int(angle_deg - JOINT_MIN_DEG)
                widgets['bar'].setValue(bar_value)

            else:
                self.get_logger().warn(f"No widget found for {placeholder_key}. Check setup.")
                break # Stop if we can't find a widget
