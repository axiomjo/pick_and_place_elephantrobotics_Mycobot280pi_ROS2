# grcn_gui_control_panel.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton

class ControlPanel(QWidget):
    """
    A dedicated widget that creates and holds all the main control buttons
    for interacting with the robot's working plane.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout for this widget
        layout = QHBoxLayout(self)

        # Create all the buttons that used to be in MainWindow
        self.send_btn = QPushButton("Send to Robot")
        self.send_btn.setDisabled(True)

        self.add_object_btn = QPushButton("Add New Object (to Plane)")
        self.reset_btn = QPushButton("Reset Plane")
        self.analyze_btn = QPushButton("Analyze (Print All)")
        self.analyze_btn.setDisabled(True)
        self.delete_btn = QPushButton("Delete Selected")
        self.rotate_counter_clockwise_btn = QPushButton("Rotate 90° CCW")
        self.rotate_clockwise_btn = QPushButton("Rotate 90° CW")

        # Add buttons to the layout in the desired order
        layout.addWidget(self.analyze_btn)
        layout.addWidget(self.delete_btn)
        layout.addStretch() # Adds a flexible space
        layout.addWidget(self.reset_btn)
        layout.addWidget(self.add_object_btn)
        layout.addWidget(self.rotate_counter_clockwise_btn)
        layout.addWidget(self.rotate_clockwise_btn)
        layout.addStretch() # Adds another flexible space
        layout.addWidget(self.send_btn)
