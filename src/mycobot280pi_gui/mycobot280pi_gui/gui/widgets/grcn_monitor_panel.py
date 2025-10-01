"""
Defines the MonitorPanel, a composite widget for displaying monitoring related controls.

This panel is ONLY a container for:
1. interactive perspective editor widget.
2. displaying annotated image widget
3. displaying joint angles widget 
It no longer displays the camera feed itself.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

# Import the child widget from the same directory

from .components.monitors.grcn_detected_objects_monitor import DetectedObjectMonitorWidget
from .components.monitors.grcn_joint_monitor import JointMonitorWidget
from .components.editors.grcn_perspective_editor import PerspectiveEditorWidget

class MonitorPanel(QWidget):
    """A widget that arranges monitoring and perspective control widgets in a specific layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Create the main vertical layout for the whole panel.
        # This will stack the top row and the bottom row.
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) # Add some padding

        # 2. Create a horizontal layout for the top row.
        top_row_layout = QHBoxLayout()

        # 3. Instantiate and add the top-left and top-right widgets.
        self.annotated_camera = DetectedObjectMonitorWidget(self)
        self.joint_monitor = JointMonitorWidget(self)
        
        top_row_layout.addWidget(self.joint_monitor)
        top_row_layout.addWidget(self.annotated_camera) # Added to the left
           

        # 4. Instantiate and configure the bottom widget.
        self.perspective_editor = PerspectiveEditorWidget(self)
        self.perspective_editor.setMinimumWidth(400) # Set the minimum width as requested.

        # 5. Add the top row and the bottom widget to the main vertical layout.
        main_layout.addLayout(top_row_layout)      # Top item
        main_layout.addWidget(self.perspective_editor) # Bottom item
