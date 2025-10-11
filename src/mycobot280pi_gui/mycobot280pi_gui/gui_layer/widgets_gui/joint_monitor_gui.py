"""
joint_monitor_gui.py - Defines the JointMonitorGUI.

This widget creates a series of labels and progress bars to show the state
of each robot joint in a human-readable format.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import pyqtSlot
from mycobot280pi_interfaces.msg import JointAnglesArray

JOINT_MIN_DEG = -170
JOINT_MAX_DEG = 170

class JointMonitorGUI(QWidget):
    """A widget that displays multiple joint states with progress bars."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        self.joint_widgets = {}
        
        # Create placeholders for 6 joints
        for i in range(1, 7):
            placeholder_key = f"joint_{i}"
            self._create_joint_display(placeholder_key, f"Joint {i}")

    def _create_joint_display(self, key, display_name): # (key: str, display_name: str)
        """Helper function to create the widgets for a single joint."""
        name_label = QLabel(f"{display_name}:")
        name_label.setFixedWidth(100)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, JOINT_MAX_DEG - JOINT_MIN_DEG)
        progress_bar.setTextVisible(False)

        value_label = QLabel("0.0°")
        value_label.setFixedWidth(60)

        joint_layout = QHBoxLayout() [cite: 246]
        joint_layout.addWidget(name_label)
        joint_layout.addWidget(progress_bar)
        joint_layout.addWidget(value_label)
        self.main_layout.addLayout(joint_layout)

        self.joint_widgets[key] = {
            'name_label': name_label,
            'bar': progress_bar,
            'value': value_label
        } [cite: 244, 247]

    @pyqtSlot(JointAnglesArray)
    def update_joint_display(self, joint_angle_msg):
        """Public slot to update all joint displays from a JointAnglesArray message."""
        latest_angles = joint_angle_msg.joint_angles
        default_joint_names = [f"Joint {i}" for i in range(1, 7)] [cite: 249]
        num_joints = min(len(latest_angles), 6)

        for i in range(num_joints):
            angle_deg = latest_angles[i]
            placeholder_key = f"joint_{i + 1}" [cite: 250]

            if placeholder_key in self.joint_widgets:
                widgets = self.joint_widgets[placeholder_key]
                widgets['name_label'].setText(f"{default_joint_names[i]}:") [cite: 251]
                widgets['value'].setText(f"{angle_deg:.1f}°") [cite: 251]
                bar_value = int(angle_deg - JOINT_MIN_DEG)
                widgets['bar'].setValue(bar_value) [cite: 252]
