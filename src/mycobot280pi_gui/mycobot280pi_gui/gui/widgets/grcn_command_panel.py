"""
REFACTOR JADI WIDGETS TIAP COMMAND

Defines the DockPanel widget.

This widget resides in the dockable area of the main window and serves three
purposes:
1. Displaying detected objects.
2. Providing controls (slider, spinbox) to adjust and SEND the rotation of a
   currently selected item.
3. Providing discrete controls to send immediate robot commands (RGB, Vacuum).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsScene, QGraphicsView,
    QSlider, QDoubleSpinBox, QGraphicsTextItem, QGroupBox, QGridLayout, 
    QPushButton, QLineEdit, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

# Type hinting for the slot method
from mycobot280pi_interfaces.msg import ManyDetectedObjects

class DockPanel(QWidget):
    """A widget for object display, rotation controls, and simple robot command controls."""
    
    # --- SIGNALS FOR MAIN WINDOW CONNECTION (to ROS Facade) ---
    
    # 1. Object Rotation Command (for RZ rotation)
    # Signal carries: (rotation_angle: float)
    send_rotation_command = pyqtSignal(float) 

    # 2. RGB Command
    # Signal carries: (r: int, g: int, b: int)
    send_rgb_command = pyqtSignal(int, int, int)
    
    # 3. Vacuum Command
    # Signal carries: (command_type: str, pin1: int, pin2: int)
    send_vacuum_command = pyqtSignal(str, int, int) 

    # Define Vacuum Pin Mapping internally (based on your V2 standard)
    VACUUM_MAP = {
        "vacuum_strong": (0, 1), # pin1=0 (MSB), pin2=1 (LSB)
        "vacuum_weak":   (0, 0),
        "vacuum_off":    (1, 0),
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Section 1: Display for Object Cutouts (Existing Logic) ---
        main_layout.addWidget(QLabel("Detected Object Cutouts:"))
        self.cutout_scene = QGraphicsScene()
        self.cutout_view = QGraphicsView(self.cutout_scene)
        self.cutout_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cutout_view.setStyleSheet("background-color: #333;")
        main_layout.addWidget(self.cutout_view, 1) # Give it stretch factor
        
        # --- Section 2: Controls for Rotation (Updated to include button) ---
        rotation_group = self._create_rotation_group()
        main_layout.addWidget(rotation_group)
        
        # --- Section 3: NEW Robot Service Commands ---
        service_cmd_group = self._create_service_command_group()
        main_layout.addWidget(service_cmd_group)

        main_layout.addStretch(1) # Push everything to the top

        # Initialize widget states
        self.update_rotation_widgets(False) 

    # --- Group Creation Helpers ---
    
    def _create_rotation_group(self):
        rotation_group = QGroupBox("Target Orientation (rz)")
        rotation_layout = QGridLayout() 

        rotation_label = QLabel("Rotation (Selected Object):")
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        
        self.rotation_spinbox = QDoubleSpinBox()
        self.rotation_spinbox.setRange(-180, 180.0)
        self.rotation_spinbox.setSingleStep(0.1)
        self.rotation_spinbox.setDecimals(1)
        self.rotation_spinbox.setSuffix(" °")
        
        # Connect slider/spinbox for display synchronization
        self.rotation_slider.valueChanged.connect(self.rotation_spinbox.setValue)
        self.rotation_spinbox.valueChanged.connect(self.rotation_slider.setValue)

        # NEW: Button to trigger the command
        self.send_rz_btn = QPushButton("APPLY RZ ROTATION")
        self.send_rz_btn.clicked.connect(self._emit_rotation_signal)

        # Layout setup
        rotation_layout.addWidget(rotation_label, 0, 0, 1, 2)
        rotation_layout.addWidget(self.rotation_slider, 1, 0)
        rotation_layout.addWidget(self.rotation_spinbox, 1, 1)
        rotation_layout.addWidget(self.send_rz_btn, 2, 0, 1, 2)
        
        rotation_group.setLayout(rotation_layout)
        return rotation_group

    def _create_service_command_group(self):
        cmd_group = QGroupBox("Immediate Robot Commands")
        vbox = QVBoxLayout()
        
        # A. RGB CONTROL
        rgb_group = QGroupBox("Set LED Color")
        rgb_layout = QHBoxLayout()
        self.r_input = QLineEdit("0"); self.r_input.setFixedWidth(40)
        self.g_input = QLineEdit("0"); self.g_input.setFixedWidth(40)
        self.b_input = QLineEdit("0"); self.b_input.setFixedWidth(40)
        send_rgb_btn = QPushButton("Set LED")
        send_rgb_btn.clicked.connect(self._emit_rgb_signal)
        
        rgb_layout.addWidget(QLabel("R:")); rgb_layout.addWidget(self.r_input)
        rgb_layout.addWidget(QLabel("G:")); rgb_layout.addWidget(self.g_input)
        rgb_layout.addWidget(QLabel("B:")); rgb_layout.addWidget(self.b_input)
        rgb_layout.addWidget(send_rgb_btn)
        rgb_group.setLayout(rgb_layout)
        vbox.addWidget(rgb_group)
        
        # B. VACUUM CONTROL
        vacuum_group = QGroupBox("Vacuum Control")
        vac_layout = QHBoxLayout()
        
        vac_strong_btn = QPushButton("Strong")
        vac_weak_btn = QPushButton("Weak")
        vac_off_btn = QPushButton("OFF")
        
        vac_strong_btn.clicked.connect(lambda: self._emit_vacuum_signal("vacuum_strong"))
        vac_weak_btn.clicked.connect(lambda: self._emit_vacuum_signal("vacuum_weak"))
        vac_off_btn.clicked.connect(lambda: self._emit_vacuum_signal("vacuum_off"))
        
        vac_layout.addWidget(vac_strong_btn)
        vac_layout.addWidget(vac_weak_btn)
        vac_layout.addWidget(vac_off_btn)
        vacuum_group.setLayout(vac_layout)
        vbox.addWidget(vacuum_group)
        
        cmd_group.setLayout(vbox)
        return cmd_group

    # --- Signal Emitters ---
    
    def _emit_rotation_signal(self):
        """Emits the signal containing the current RZ spinbox value for the selected object."""
        current_rz = self.rotation_spinbox.value()
        self.send_rotation_command.emit(current_rz)

    def _emit_rgb_signal(self):
        """Emits the signal for RGB command."""
        try:
            r = int(self.r_input.text())
            g = int(self.g_input.text())
            b = int(self.b_input.text())
            
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                self.send_rgb_command.emit(r, g, b)
            else:
                self.r_input.setText("0"); self.g_input.setText("0"); self.b_input.setText("0")
        except ValueError:
            pass # Ignore invalid input for safety

    def _emit_vacuum_signal(self, command_key: str):
        """Emits the signal for vacuum command based on the key."""
        pin1, pin2 = self.VACUUM_MAP.get(command_key, (1, 1)) # Default to off
        self.send_vacuum_command.emit(command_key, pin1, pin2)


    # --- Public Methods (Slots) ---

    
    def update_object_count(self, objects_msg: ManyDetectedObjects):
        """
        Public slot that receives detected objects data from MainWindow.
        """
        self.cutout_scene.clear()
        
        if not objects_msg or not objects_msg.objects:
            text_item = QGraphicsTextItem("No objects detected.")
            text_item.setDefaultTextColor(Qt.white)
            self.cutout_scene.addItem(text_item)
            return

        count = len(objects_msg.objects)
        text_item = QGraphicsTextItem(f"Detected {count} object(s).")
        text_item.setDefaultTextColor(Qt.white)
        self.cutout_scene.addItem(text_item)

    
    def update_rotation_widgets(self, is_item_selected: bool, rotation_value: float = 0):
        """
        Public slot to enable/disable rotation controls and set their value.
        This is called by MainWindow when the selection on the WorkingPlane changes.
        """
        self.rotation_slider.setDisabled(not is_item_selected)
        self.rotation_spinbox.setDisabled(not is_item_selected)
        self.send_rz_btn.setDisabled(not is_item_selected) # Disable the button too!

        if is_item_selected:
            self.rotation_spinbox.blockSignals(True)
            self.rotation_slider.blockSignals(True)
            
            # The QSlider range is -180 to 180, so we pass the float value directly 
            # to the spinbox, and the spinbox updates the slider (integer value is close enough).
            self.rotation_spinbox.setValue(rotation_value)
            
            self.rotation_spinbox.blockSignals(False)
            self.rotation_slider.blockSignals(False)
