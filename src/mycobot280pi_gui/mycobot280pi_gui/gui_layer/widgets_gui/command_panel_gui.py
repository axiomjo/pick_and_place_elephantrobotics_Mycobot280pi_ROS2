"""
command_panel_gui.py - Defines the CommandPanelGUI widget.

This View is the dockable panel that provides direct control over the robot's
pose, speed, LEDs, and vacuum pump. It emits signals based on user interaction,
which are then handled by the SimpleCommandHandler.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsScene, QGraphicsView,
    QSlider, QDoubleSpinBox, QSpinBox, QGroupBox, QGridLayout, 
    QPushButton, QLineEdit, QHBoxLayout, QGraphicsTextItem
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

# Import message type for type hinting the slot
from mycobot280pi_interfaces.msg import ManyDetectedObjects

class CommandPanelGUI(QWidget):
    """The View for all direct robot control widgets."""
    
    # --- Public Signals (Outputs for the Controller) ---
    send_coords_command = pyqtSignal(float, float, float, float, float, float, int)
    send_home_command = pyqtSignal()
    send_rgb_command = pyqtSignal(int, int, int)
    send_vacuum_command = pyqtSignal(str, int, int)
    
    # --- Internal Constants ---
    VACUUM_MAP = {
        "vacuum_strong": (0, 1),
        "vacuum_weak":   (0, 0),
        "vacuum_off":    (1, 0),
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.sliders = {}
        self.spinboxes = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Section 1: Detected Object Cutouts Display
        main_layout.addWidget(QLabel("Detected Object Cutouts:"))
        self.cutout_scene = QGraphicsScene()
        self.cutout_view = QGraphicsView(self.cutout_scene)
        self.cutout_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cutout_view.setStyleSheet("background-color: #333;")
        main_layout.addWidget(self.cutout_view, 1) # Give stretch factor
        
        # Section 2: Target Pose & Speed Controls
        target_pose_group = self._create_target_pose_group()
        main_layout.addWidget(target_pose_group)
        
        # Section 3: Other Immediate Commands
        service_cmd_group = self._create_service_command_group()
        main_layout.addWidget(service_cmd_group)

        main_layout.addStretch(1)
        
        # Initially, disable all sliders until an object is selected
        self.update_target_sliders_from_selection(None)

    # --- UI Helper Methods (Copied from old project, no logic change) ---
    def _create_target_pose_group(self):
        group = QGroupBox("Target Pose & Speed")
        layout = QGridLayout()

        widget_configs = [
            {'name': 'X',  'unit': 'mm', 'range': (-280.0, 280.0), 'decimals': 1, 'type': 'double'},
            {'name': 'Y',  'unit': 'mm', 'range': (-280.0, 280.0), 'decimals': 1, 'type': 'double'},
            {'name': 'Z',  'unit': 'mm', 'range': (45.0, 400.0),   'decimals': 1, 'type': 'double'},
            {'name': 'RX', 'unit': '°',  'range': (-180.0, 180.0), 'decimals': 1, 'type': 'double'},
            {'name': 'RY', 'unit': '°',  'range': (-180.0, 180.0), 'decimals': 1, 'type': 'double'},
            {'name': 'RZ', 'unit': '°',  'range': (-180.0, 180.0), 'decimals': 1, 'type': 'double'},
            {'name': 'Speed','unit': '%', 'range': (10, 100),       'decimals': 0, 'type': 'int'},
        ]

        for i, config in enumerate(widget_configs):
            name = config['name']
            min_val, max_val = config['range']
            
            label = QLabel(f"{name}:")
            slider = QSlider(Qt.Horizontal)
            
            if config['type'] == 'double':
                spinbox = QDoubleSpinBox()
                spinbox.setDecimals(config['decimals'])
                scale = 10**config['decimals']
                slider.setRange(int(min_val * scale), int(max_val * scale))
                slider.valueChanged.connect(lambda val, s=spinbox, sc=scale: s.setValue(val / sc))
                spinbox.valueChanged.connect(lambda val, s=slider, sc=scale: s.setValue(int(val * sc)))
            else: # 'int'
                spinbox = QSpinBox()
                slider.setRange(min_val, max_val)
                slider.valueChanged.connect(spinbox.setValue)
                spinbox.valueChanged.connect(slider.setValue)

            spinbox.setRange(min_val, max_val)
            spinbox.setSingleStep(0.1 if config['type'] == 'double' else 1)
            spinbox.setSuffix(f" {config['unit']}")
            
            
          
            self.sliders[name] = slider
            self.spinboxes[name] = spinbox
            
            layout.addWidget(label, i, 0)
            layout.addWidget(slider, i, 1)
            layout.addWidget(spinbox, i, 2)
            
        self.send_coords_btn = QPushButton("SEND FULL POSE TO ROBOT")
        self.send_coords_btn.clicked.connect(self._emit_coords_signal)
        layout.addWidget(self.send_coords_btn, len(widget_configs), 0, 1, 3)

        self.go_home_btn = QPushButton("GO HOME")
        self.go_home_btn.setStyleSheet("background-color: #E74C3C; color: green;")
        self.go_home_btn.clicked.connect(self._emit_home_signal)
        
        # Gunakan baris berikutnya setelah SEND FULL POSE
        layout.addWidget(self.go_home_btn, len(widget_configs) + 1, 0, 1, 3) 


        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group
    
    def _create_service_command_group(self):
        # Method ini sudah bagus, tidak perlu diubah
        # ... (salin-tempel method _create_service_command_group Anda di sini) ...
        cmd_group = QGroupBox("Immediate Robot Commands")
        vbox = QVBoxLayout()
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

    # --- Private Signal Emitters (Copied from old project) ---

    def _emit_coords_signal(self):
        vals = {name: spinbox.value() for name, spinbox in self.spinboxes.items()}
        self.send_coords_command.emit(vals['X'], vals['Y'], vals['Z'], vals['RX'], vals['RY'], vals['RZ'], vals['Speed'])

    def _emit_home_signal(self):
        self.send_home_command.emit()

    def _emit_rgb_signal(self):
        try:
            r, g, b = int(self.r_input.text()), int(self.g_input.text()), int(self.b_input.text())
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255: self.send_rgb_command.emit(r, g, b)
        except ValueError: pass

    def _emit_vacuum_signal(self, command_key): # (command_key: str)
        pin1, pin2 = self.VACUUM_MAP.get(command_key, (1, 1))
        self.send_vacuum_command.emit(command_key, pin1, pin2)

    # --- Public Slots (Inputs from other components) ---

    @pyqtSlot(ManyDetectedObjects)
    def update_object_count(self, objects_msg):
        """Public slot to update the text in the cutout view."""
        self.cutout_scene.clear()
        if not objects_msg or not objects_msg.objects:
            text = "No objects detected."
        else:
            text = "Detected {} object(s).".format(len(objects_msg.objects))
        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(Qt.white)
        self.cutout_scene.addItem(text_item)
        
    @pyqtSlot(list)
    def update_target_sliders_from_selection(self, selected_items):
        """
        Public slot. Updates sliders based on the selected item in the workspace.
        """
        is_item_selected = selected_items is not None and len(selected_items) == 1

        for widget in list(self.sliders.values()) + list(self.spinboxes.values()):
            widget.setEnabled(is_item_selected)
        self.send_coords_btn.setEnabled(is_item_selected)

        if not is_item_selected:
            return
        
        try:
            item = selected_items[0]
            x, y, z, rx, ry, rz = item.get_pose()
            pose = {'X': x, 'Y': y, 'Z': z, 'RX': rx, 'RY': ry, 'RZ': rz}
            for name, value in pose.items():
                self._set_synced_value(name, value)
        except AttributeError:
            print("Error: Selected item does not have a get_pose() method.")

    def _set_synced_value(self, name, value):
        spinbox, slider = self.spinboxes.get(name), self.sliders.get(name)
        if not spinbox or not slider: return
        spinbox.blockSignals(True); slider.blockSignals(True)
        spinbox.setValue(value)
        if isinstance(spinbox, QDoubleSpinBox):
            slider.setValue(int(value * (10**spinbox.decimals())))
        else:
            slider.setValue(int(value))
        spinbox.blockSignals(False); slider.blockSignals(False)
