
"""
Defines the DockPanel widget.

This widget resides in the dockable area of the main window and serves two
specialized purposes:
1.  Displaying image cutouts of all detected objects in a scene.
2.  Providing controls (a slider and spinbox) to adjust the rotation of a
    currently selected item on the WorkingPlane.

Like other widgets, it is a passive component controlled by the MainWindow.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsScene, QGraphicsView,
    QSlider, QDoubleSpinBox, QGraphicsTextItem
)
from PyQt5.QtCore import Qt

# Type hinting for the slot method
from mycobot280pi_interfaces.msg import ManyDetectedObjects

# This widget has no direct dependency on ROS, but it will need the utility
# function to create pixmaps from image data provided by MainWindow.
# We assume MainWindow will pass the necessary data.

class DockPanel(QWidget):
    """A widget for displaying object cutouts and rotation controls."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # The main layout for this panel is vertical
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Section 1: Display for Object Cutouts ---
        cutout_label = QLabel("Detected Object Cutouts:")
        self.cutout_scene = QGraphicsScene()
        self.cutout_view = QGraphicsView(self.cutout_scene)
        self.cutout_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cutout_view.setStyleSheet("background-color: #333;")
        
        main_layout.addWidget(cutout_label)
        main_layout.addWidget(self.cutout_view, 1) # Give it stretch factor
        
        # --- Section 2: Controls for Rotation ---
        rotation_label = QLabel("Rotation (Selected Object):")
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        
        self.rotation_spinbox = QDoubleSpinBox()
        self.rotation_spinbox.setRange(-180, 180.0)
        self.rotation_spinbox.setSingleStep(0.1)
        self.rotation_spinbox.setDecimals(1)
        self.rotation_spinbox.setSuffix(" °")
        
        # Connect the slider and spinbox to always show the same value
        self.rotation_slider.valueChanged.connect(self.rotation_spinbox.setValue)
        self.rotation_spinbox.valueChanged.connect(self.rotation_slider.setValue)

        # Add the rotation controls to the layout
        main_layout.addWidget(rotation_label)
        main_layout.addWidget(self.rotation_slider)
        main_layout.addWidget(self.rotation_spinbox)
        
        # The controls should be disabled until an object is selected
        self.rotation_slider.setDisabled(True)
        self.rotation_spinbox.setDisabled(True)

    # --- Public Methods (Slots) for MainWindow to Call ---

    def update_object_count(self, objects_msg: ManyDetectedObjects):
        """
        Public slot that receives detected objects data from MainWindow.
        
        Note: This implementation is a placeholder. A full implementation would
        also receive the source image to generate pixmap cutouts.
        """
        self.cutout_scene.clear()
        
        if not objects_msg or not objects_msg.objects:
            text_item = QGraphicsTextItem("No objects detected.")
            text_item.setDefaultTextColor(Qt.white)
            self.cutout_scene.addItem(text_item)
            return

        # Display a summary of the detected objects
        count = len(objects_msg.objects)
        text_item = QGraphicsTextItem(f"Detected {count} object(s).")
        text_item.setDefaultTextColor(Qt.white)
        self.cutout_scene.addItem(text_item)
        # A full implementation would now loop through objects, call
        # create_cutout_pixmap, and add the resulting pixmaps to the scene.


    def update_rotation_widgets(self, is_item_selected: bool, rotation_value: float = 0):
        """
        Public slot to enable/disable rotation controls and set their value.
        This is called by MainWindow when the selection on the WorkingPlane changes.
        """
        self.rotation_slider.setDisabled(not is_item_selected)
        self.rotation_spinbox.setDisabled(not is_item_selected)

        if is_item_selected:
            # Temporarily block signals to prevent a feedback loop when setting the value.
            # This is a standard and important practice in Qt.
            self.rotation_spinbox.blockSignals(True)
            self.rotation_slider.blockSignals(True)
            
            self.rotation_spinbox.setValue(rotation_value)
            
            # Re-enable signals after setting the value.
            self.rotation_spinbox.blockSignals(False)
            self.rotation_slider.blockSignals(False)
