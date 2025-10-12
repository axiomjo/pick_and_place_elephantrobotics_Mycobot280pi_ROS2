"""
monitor_panel_gui.py - Defines the MonitorPanelGUI.

This panel is a container View. Its only job is to instantiate and arrange
the other monitoring-related widgets, such as the camera feeds and joint monitor.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

# Import the child widget Views it will contain
from .detected_objects_monitor_gui import DetectedObjectMonitorGUI
from .joint_monitor_gui import JointMonitorGUI
from .perspective_editor_gui import PerspectiveEditorGUI

class MonitorPanelGUI(QWidget):
    """A widget that arranges monitoring widgets in a specific layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self) 
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 1. Create a horizontal layout for the top row.
        top_row_layout = QHBoxLayout()

        # 2. Instantiate the child widgets.
        self.annotated_camera = DetectedObjectMonitorGUI(self)
        self.joint_monitor = JointMonitorGUI(self)
        self.perspective_editor = PerspectiveEditorGUI(self)
        
        # 3. Add the top-row widgets to the horizontal layout.
        top_row_layout.addWidget(self.joint_monitor)
        top_row_layout.addWidget(self.annotated_camera)
           
        # 4. Add the top row layout and the bottom widget to the main vertical layout.
        main_layout.addLayout(top_row_layout)
        main_layout.addWidget(self.perspective_editor)
