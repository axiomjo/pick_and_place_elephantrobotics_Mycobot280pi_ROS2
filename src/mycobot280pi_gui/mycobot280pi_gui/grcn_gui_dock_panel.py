# grcn_gui_dock_panel.py
"""
Defines the content for the dockable panel on the right side of the GUI.

This widget is a "specialist" responsible for creating the UI elements for
displaying detected object cutouts and for controlling the rotation of a
selected item on the main working plane.
"""
# Standard Python Libraries
import cv2
from cv_bridge import CvBridge

# Third-Party Libraries
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsScene, QGraphicsView,
    QSlider, QDoubleSpinBox
)
from PyQt5.QtCore import Qt

# Custom ROS 2 Interfaces
from mycobot280pi_interfaces.msg import ManyDetectedObjects

from .grcn_pyqt_widget import create_cutout_pixmap


class DockPanel(QWidget):
    """
    This class builds the widget containing the cutout
    view and rotation controls.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bridge = CvBridge()

        # The main layout for our cabinet is vertical (top to bottom)
        main_layout = QVBoxLayout(self)

        # --- Section 1: The "Display Shelves" for Object Cutouts ---
        cutout_label = QLabel("Detected Object Cutouts:")
        self.cutout_scene = QGraphicsScene()
        self.cutout_view = QGraphicsView(self.cutout_scene)
        self.cutout_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        main_layout.addWidget(cutout_label)
        main_layout.addWidget(self.cutout_view)
        
        # --- Section 2: The "Control Knobs" for Rotation ---
        rotation_label = QLabel("Rotation (Selected Object):")
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        
        self.rotation_spinbox = QDoubleSpinBox()
        self.rotation_spinbox.setRange(-180, 180)
        self.rotation_spinbox.setSingleStep(0.1)
        self.rotation_spinbox.setDecimals(1)
        
        # We connect the slider and spinbox so they always show the same value
        self.rotation_slider.valueChanged.connect(self.rotation_spinbox.setValue)
        self.rotation_spinbox.valueChanged.connect(self.rotation_slider.setValue)

        # Add the rotation controls to the layout
        main_layout.addWidget(rotation_label)
        main_layout.addWidget(self.rotation_slider)
        main_layout.addWidget(self.rotation_spinbox)
        
        # The knobs should be disabled until an object is selected
        self.rotation_slider.setDisabled(True)
        self.rotation_spinbox.setDisabled(True)

    # --- Public Methods (Slots) for MainWindow to Call ---

    def update_object_cutouts(self, source_image, objects_msg: ManyDetectedObjects):
        """
        Receives a ready-to-use OpenCV image and object data from MainWindow
        to generate and display the cutouts.
        """
        
        self.cutout_scene.clear()
        
        if source_image is None or not objects_msg.objects:
            self.cutout_scene.addText("No objects detected.")
            return

        y_offset = 0
        
        for obj in objects_msg.objects:
            pixmap = create_cutout_pixmap(source_image, obj)
            
            if not pixmap.isNull():
                pixmap_item = self.cutout_scene.addPixmap(pixmap)
                pixmap_item.setPos(0, y_offset)
                y_offset += pixmap.height() + 5
                
        # Placeholder text until conversion is fully implemented
        self.cutout_scene.addText(f"Received {len(objects_msg.objects)} objects.")

    def update_rotation_widgets(self, is_item_selected: bool, rotation_value: float = 0):
        """
        The General Contractor (MainWindow) calls this to enable/disable
        the knobs and set their position.
        """
        self.rotation_slider.setDisabled(not is_item_selected)
        self.rotation_spinbox.setDisabled(not is_item_selected)

        if is_item_selected:
            # Temporarily disconnect signals to prevent feedback loops when setting value
            self.rotation_spinbox.blockSignals(True)
            self.rotation_slider.blockSignals(True)
            
            self.rotation_spinbox.setValue(rotation_value)
            
            # Reconnect signals
            self.rotation_spinbox.blockSignals(False)
            self.rotation_slider.blockSignals(False)
