#!/usr/bin/env python3

"""
Defines the ActionPanel, a dedicated widget for the main action buttons.
"""

# Impor QGridLayout
from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout

class ActionPanel(QWidget):
    """A container widget that holds all the main control buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ### DIUBAH: Gunakan QGridLayout ###
        layout = QGridLayout(self)

        # Create all the button instances

        self.add_object_btn = QPushButton("Add New Objects")
        self.reset_btn = QPushButton("Reset Plane")
        self.analyze_btn = QPushButton("Start Pick & Place")
        self.emergency_btn = QPushButton("Cancel Action")
        self.delete_btn = QPushButton("Delete Selected")
        self.rotate_counter_clockwise_btn = QPushButton("Rotate CCW")
        self.rotate_clockwise_btn = QPushButton("Rotate CW")
        
        # Disable buttons that should only be enabled by the state machine
 
        self.emergency_btn.setEnabled(False)

        # ### DIUBAH: Tambahkan tombol ke grid (baris, kolom) ###
        
        # Baris 0: Tombol Aksi Utama
        # Kita buat tombol Start lebih besar dengan membuatnya memakan 2 kolom (colSpan=2)
        layout.addWidget(self.analyze_btn, 0, 0, 1, 2) # Baris 0, Kolom 0, memakan 1 baris, 2 kolom
        layout.addWidget(self.emergency_btn, 0, 2)      # Baris 0, Kolom 2
        layout.addWidget(self.delete_btn, 0, 3)         # Baris 0, Kolom 3

        # Baris 1: Tombol Utilitas
        layout.addWidget(self.reset_btn, 1, 0)          # Baris 1, Kolom 0
        layout.addWidget(self.add_object_btn, 1, 1)     # Baris 1, Kolom 1
        layout.addWidget(self.rotate_counter_clockwise_btn, 1, 2) # Baris 1, Kolom 2
        layout.addWidget(self.rotate_clockwise_btn, 1, 3)     # Baris 1, Kolom 3


        # ### DIUBAH: Cara baru untuk menambahkan spasi fleksibel ###
        # Beri ruang ekstra pada kolom antara tombol aksi dan utilitas jika ada ruang lebih
        layout.setColumnStretch(4, 1) # Memberi "stretch" pada kolom ke-4 (indeks dari 0)
