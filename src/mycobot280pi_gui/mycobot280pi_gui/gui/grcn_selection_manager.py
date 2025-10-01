# File: grcn_selection_manager.py (Versi Refactored)

from PyQt5.QtCore import QObject, pyqtSignal

# ### LANGKAH 1: PASTIKAN CLASS MEWARISI QObject ###
class SelectionManager(QObject):
    
    # ### LANGKAH 2: DEFINISIKAN SINYAL DENGAN BENAR ###
    # Sinyal ini akan menjadi satu-satunya "output" dari manager ini.
    selection_changed = pyqtSignal(object)

    def __init__(self, main_window):
        # Inisialisasi QObject
        super().__init__()
        
        self.main_window = main_window
        self.logger = main_window.logger
        self.selected_item = None

    
    # Method ini adalah "pintu masuk" baru untuk manager ini.
    def set_selected_item(self, item):
        """
        Slot publik. Dipanggil dari luar (oleh scene) saat item dipilih.
        Tugasnya adalah mencatat item dan mengumumkan perubahan.
        """
        self.selected_item = item
        
        # (Opsional) Anda tetap bisa memperbarui status bar dari sini
        if item and hasattr(item, 'get_pose'):
            x, y, _, _, _, rz = item.get_pose()
            self.main_window.statusBar().showMessage(f"Selected item at ({x:.1f}, {y:.1f}) with rotation {rz:.1f}°")
        
       
        # Umumkan ke seluruh aplikasi bahwa item baru telah dipilih.
        self.selection_changed.emit(self.selected_item)


    def clear_selection(self):
        """Slot publik untuk membersihkan seleksi."""
        if self.selected_item:
            # Beritahu item grafisnya sendiri bahwa ia tidak lagi dipilih
            self.selected_item.setSelected(False)
        self.selected_item = None
        self.main_window.statusBar().showMessage("Selection cleared.")

        # Umumkan juga saat tidak ada yang dipilih
        self.selection_changed.emit(None)

    def get_selected_item(self):
        return self.selected_item
