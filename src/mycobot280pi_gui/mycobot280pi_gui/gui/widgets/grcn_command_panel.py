from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGraphicsScene, QGraphicsView,
    QSlider, QDoubleSpinBox, QSpinBox, QGroupBox, QGridLayout, 
    QPushButton, QLineEdit, QHBoxLayout,QGraphicsTextItem
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

# Hapus atau sesuaikan import ini jika tidak digunakan lagi di file ini
from mycobot280pi_interfaces.msg import ManyDetectedObjects

class CommandPanel(QWidget):
    """
    Panel kontrol untuk menampilkan info, memanipulasi pose visual,
    dan mengirim perintah ke robot.
    """
    
    # --- SINYAL UNTUK DIHUBUNGKAN KE LUAR ---

    # Sinyal untuk mengirim perintah pose lengkap ke robot
    send_coords_command = pyqtSignal(float, float, float, float, float, float, int)
    send_home_command = pyqtSignal(bool)
    
    # Sinyal untuk perintah sederhana lainnya
    send_rgb_command = pyqtSignal(int, int, int)
    send_vacuum_command = pyqtSignal(str, int, int)
    
    VACUUM_MAP = {
        "vacuum_strong": (0, 1),
        "vacuum_weak":   (0, 0),
        "vacuum_off":    (1, 0),
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        # Inisialisasi dictionary untuk menyimpan referensi ke widget
        self.sliders = {}
        self.spinboxes = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Section 1: Display Info (Cutouts) ---
        main_layout.addWidget(QLabel("Detected Object Cutouts:"))
        self.cutout_scene = QGraphicsScene()
        self.cutout_view = QGraphicsView(self.cutout_scene)
        self.cutout_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cutout_view.setStyleSheet("background-color: #333;")
        main_layout.addWidget(self.cutout_view, 1) # Beri stretch factor
        
        # --- Section 2: Target Pose (Grup Slider Utama) ---
        # Kita gabungkan semua slider menjadi satu grup yang rapi
        target_pose_group = self._create_target_pose_group()
        main_layout.addWidget(target_pose_group)
        
        # --- Section 3: Perintah Langsung Lainnya ---
        service_cmd_group = self._create_service_command_group()
        main_layout.addWidget(service_cmd_group)

        main_layout.addStretch(1)
        
        # Awalnya, nonaktifkan semua slider sampai ada objek yang dipilih
        self.update_target_sliders_from_selection(None)

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


    # --- Signal Emitters ---
    def _emit_coords_signal(self):
        """Mengirim sinyal dengan nilai dari semua 7 spinbox target."""
        vals = {name: spinbox.value() for name, spinbox in self.spinboxes.items()}
        self.send_coords_command.emit(
            vals['X'], vals['Y'], vals['Z'], 
            vals['RX'], vals['RY'], vals['RZ'], 
            vals['Speed']
        )

    def _emit_home_signal(self):
        """Mengirim sinyal angka konstan"""
        self.send_home_command.emit(0)


    # ... (method _emit_rgb_signal dan _emit_vacuum_signal Anda tetap sama) ...
    def _emit_rgb_signal(self):
        try:
            r = int(self.r_input.text()); g = int(self.g_input.text()); b = int(self.b_input.text())
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255: self.send_rgb_command.emit(r, g, b)
        except ValueError: pass

    def _emit_vacuum_signal(self, command_key: str):
        pin1, pin2 = self.VACUUM_MAP.get(command_key, (1, 1))
        self.send_vacuum_command.emit(command_key, pin1, pin2)
        

    def _set_synced_value(self, name, value):
        """
        Mengatur nilai untuk sepasang spinbox dan slider, memastikan keduanya sinkron.
        """
        if name not in self.spinboxes or name not in self.sliders:
            return # Pengaman jika nama tidak ada

        spinbox = self.spinboxes[name]
        slider = self.sliders[name]

        # Blokir sinyal dari KEDUA widget untuk sementara
        spinbox.blockSignals(True)
        slider.blockSignals(True)

        # Atur nilai spinbox secara langsung
        spinbox.setValue(value)

        # Hitung dan atur nilai slider yang sesuai
        if isinstance(spinbox, QDoubleSpinBox):
            scale = 10**spinbox.decimals()
            slider.setValue(int(value * scale))
        else: # QSpinBox
            slider.setValue(int(value))

        # Lepaskan blokir sinyal
        spinbox.blockSignals(False)
        slider.blockSignals(False)




    # --- Public Methods (Slots) ---
    def update_object_count(self, objects_msg: ManyDetectedObjects):
        # ... (method ini tetap sama) ...
        self.cutout_scene.clear()
        if not objects_msg or not objects_msg.objects: text_item = QGraphicsTextItem("No objects detected.")
        else: text_item = QGraphicsTextItem(f"Detected {len(objects_msg.objects)} object(s).")
        text_item.setDefaultTextColor(Qt.white)
        self.cutout_scene.addItem(text_item)


    # ### INI ADALAH SLOT UTAMA YANG BARU ###
    def update_target_sliders_from_selection(self, selected_item):
        """
        Slot publik. Dipanggil ketika item di WorkspacePlane dipilih.
        Memperbarui semua slider dengan data pose dari item yang dipilih.
        """
        is_item_selected = selected_item is not None

        # Aktifkan/nonaktifkan semua widget berdasarkan seleksi
        for widget_dict in [self.sliders, self.spinboxes]:
            for widget in widget_dict.values():
                widget.setEnabled(is_item_selected)
        self.send_coords_btn.setEnabled(is_item_selected)

        if not is_item_selected:
            return

        try:
            x, y, z, rx, ry, rz = selected_item.get_pose()
            pose = {'X': x, 'Y': y, 'Z': z, 'RX': rx, 'RY': ry, 'RZ': rz}
            
            # ### DIUBAH: Gunakan helper method kita ###
            # Loop melalui data pose dan panggil helper untuk setiap pasang widget
            for name, value in pose.items():
                if name in self.spinboxes:
                    self._set_synced_value(name, value)

        except AttributeError:
            print(f"Error: Item yang dipilih tidak memiliki method get_pose().")
            
            
            
            
