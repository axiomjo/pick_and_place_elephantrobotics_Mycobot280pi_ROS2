import cv2 # Make sure cv2 is imported
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget, QMessageBox
from PyQt5.QtGui import QImage, QPixmap, QTransform
from PyQt5.QtCore import Qt

# from other grcn files
from .grcn_gui_camera_panel import CameraPanel
from .grcn_gui_working_plane import WorkingPlane
from .grcn_gui_control_panel import ControlPanel
from .grcn_gui_dock_panel import DockPanel
from .grcn_pyqt_widget import create_cutout_pixmap, DraggableItem

from mycobot280pi_interfaces.msg import OneDetectedObject, ManyDetectedObjects, Point2DArray, Point2D # Impor pesan yang dibutuhkan

class MainWindow(QMainWindow):
    def __init__(self, ros_comm):
    
        
        super().__init__()
        
        # 1. Assign ros_comm to self so the object knows about it.
        self.ros_comm = ros_comm
        
        # 2. NOW that self.ros_comm exists, we can get the logger from it.
        self.logger = self.ros_comm.get_logger()

        self.setWindowTitle("MyCobot 280 Pi GUI")
        self.resize(1400, 900)

        self.ros_comm = ros_comm
        self.latest_objects_msg = None
        self.latest_annotated_image = None
        
        # --- GUI Panels ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.camera_panel = CameraPanel(self.ros_comm)
        self.working_plane = WorkingPlane()
        self.control_panel = ControlPanel()
        self.dock_panel_widget = DockPanel()
        
        # --- BUG FIX: The items_on_plane list is removed from MainWindow ---

        # --- Layout Assembly ---
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.working_plane)
        right_layout.addWidget(self.control_panel)
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(self.camera_panel, 1)
        main_layout.addLayout(right_layout, 2)

        # --- Dock Widget ---
        dock = QDockWidget("Controls & Cutouts", self)
        dock.setWidget(self.dock_panel_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
       
        self.connect_signals()
        self.statusBar().showMessage("GUI is Ready.")
        
    def connect_signals(self):
        # ROS Facade -> MainWindow Slots
        self.ros_comm.detected_objects_received.connect(self.cache_detected_objects)
        self.ros_comm.annotated_image_received.connect(self.cache_annotated_image)
        self.ros_comm.simple_command_response.connect(self.on_simple_command_response)
        
        self.ros_comm.action_feedback.connect(self._action_feedback)
        self.ros_comm.action_result.connect(self._action_result)
        
        # Control Panel Buttons -> MainWindow Logic
        self.control_panel.analyze_btn.clicked.connect(self._on_start_action)
        self.control_panel.emergency_btn.clicked.connect(self._on_cancel_action)
        self.control_panel.send_btn.clicked.connect(self.send_service_request)
        self.control_panel.reset_btn.clicked.connect(self.reset_plane)
        self.control_panel.add_object_btn.clicked.connect(self.add_new_objects_from_cutouts)
        self.control_panel.analyze_btn.clicked.connect(self.analyze_positions)
        self.control_panel.delete_btn.clicked.connect(self.delete_selected)
        
        # When an item is selected in the working plane, call our new update method
        self.working_plane.working_plane_scene.selectionChanged.connect(self.update_status_bar_with_selection)
        
        # rotation stuff
        self.control_panel.rotate_clockwise_btn.clicked.connect(self.working_plane.rotate_clockwise)
        self.control_panel.rotate_counter_clockwise_btn.clicked.connect(self.working_plane.rotate_counter_clockwise)

    # --- Data Caching ---
    def cache_detected_objects(self, objects_msg: ManyDetectedObjects):
        self.latest_objects_msg = objects_msg
        if self.dock_panel_widget and self.latest_annotated_image is not None:
            self.dock_panel_widget.update_object_count(objects_msg)
            
    def cache_annotated_image(self, cv_image):
        self.latest_annotated_image = cv_image
        self.camera_panel.update_camera_view(cv_image)

    # --- High-Level Logic Methods ---
    def reset_plane(self):
        # Now we call a high-level method on the working plane widget
        self.working_plane.reset_scene()

    def add_new_objects_from_cutouts(self):
    
        objects_to_process = self.latest_objects_msg
        image_to_process = self.latest_annotated_image
        
        if self.latest_objects_msg is None or self.latest_annotated_image is None:
            self.logger.warn("Add objects called, but data is not ready yet.")
            self.statusBar().showMessage("Data not available to add objects.")
            return
            

        img_height, img_width, _ = image_to_process.shape
        cam_center_x = img_width / 2.0
        cam_center_y = img_height / 2.0
        
        
        for obj in self.latest_objects_msg.objects:
            try:

                
                self.logger.info(f"--- Processing Object ID {obj.id} ---")

                pixmap = create_cutout_pixmap(image_to_process, obj)
                if pixmap.isNull(): continue
                
                transform = QTransform()
                transform.scale(1, -1)
                flipped_pixmap = pixmap.transformed(transform)
                if flipped_pixmap.isNull(): continue
                

                item = DraggableItem(
                    pixmap=flipped_pixmap, 
                    object_id=obj.id
                )
                
                obj_center_x = obj.center_point.x
                obj_center_y = obj.center_point.y
                
                scene_x = obj_center_x - cam_center_x
                scene_y = -(obj_center_y - cam_center_y)
                
                final_x = scene_x - (flipped_pixmap.width() / 2)
                final_y = scene_y - (flipped_pixmap.height() / 2)
                
                item.setPos(final_x, final_y)
                
                self.working_plane.working_plane_scene.addItem(item)
                
                self.working_plane.items_on_plane.append(item)
                self.logger.info(f"--- Finished Object ID {obj.id} ---")

            except Exception as e:
                # This is our existing, detailed exception reporter
                error_msg = f"ERROR on obj {obj.id}: {type(e).__name__}. See terminal."
                self.statusBar().showMessage(error_msg, 5000)
                
                self.logger.error("\n" + "="*20)
                self.logger.error(f"CAUGHT EXCEPTION: {type(e).__name__} - {e}")
                self.logger.error(f"Problem occurred on Object ID: {obj.id}")
                self.logger.error("--- Dumping Problematic Object Data ---")
                self.logger.error(f"{obj}")
                self.logger.error("="*20 + "\n")
        success_msg = f"Finished processing. Added {len(self.working_plane.items_on_plane)} objects to the plane."
        #self.statusBar().showMessage(success_msg)
        
    def send_service_request(self):
        # --- BUG FIX: Use the correct scene name ---
        selected_items = self.working_plane.working_plane_scene.selectedItems()
        if not selected_items:
            print("No item selected.")
            return
        item = selected_items[0]
        if not isinstance(item, DraggableItem):
            return

        robot_target_id = item.object_id
        
        center_pos = item.mapToScene(item.boundingRect().center())
        rot = item.rotation()
        coords = [center_pos.x(), center_pos.y(), 60.0, 180.0, 0.0, rot]
        
        self.ros_comm.call_simple_command(coords=coords, speed=80, is_linear_mode=False)
        
    def on_simple_command_response(self, success: bool, message: str):
        # Here you would update a status bar or enable/disable buttons.
        self.control_panel.send_btn.setDisabled(False) # Example
        self.control_panel.analyze_btn.setDisabled(False) # Example

    def analyze_positions(self):
        # --- BUG FIX: Use the list from the working_plane object ---
        for i, item in enumerate(self.working_plane.items_on_plane, start=1):
            pos = item.scenePos()
            rot = item.rotation()
         

    def update_status_bar_with_selection(self):
        """
        Called whenever the selection changes in the working_plane_scene.
        Updates the status bar with the details of the selected item.
        """
        # Get the list of all currently selected items
        selected_items = self.working_plane.working_plane_scene.selectedItems()

        if not selected_items:
            # If the list is empty, it means nothing is selected
            self.statusBar().showMessage("No item selected.")
            return

        # We'll just focus on the first selected item
        item = selected_items[0]

        # Make sure it's a DraggableItem before we try to access its properties
        if isinstance(item, DraggableItem):
            pos = item.mapToScene(item.boundingRect().center())
            rot = item.rotation()

            # Create a nicely formatted string with the item's info
            message = (
                f"Selected Item ID: {item.object_id} | "
                f"Position: (X={pos.x():.1f}, Y={pos.y():.1f}) | "
                f"Rotation: {rot:.1f}°"
            )
            
            # Display the message in the status bar
            self.statusBar().showMessage(message)
    
    def delete_selected(self):
        # --- BUG FIX: Use the correct scene name ---
        selected_items = self.working_plane.working_plane_scene.selectedItems()
        for item in selected_items:
            # --- BUG FIX: Remove from the correct list ---
            self.working_plane.working_plane_scene.removeItem(item)
            if item in self.working_plane.items_on_plane:
                self.working_plane.items_on_plane.remove(item)
       
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    # ----------------- GUI Slots -----------------
    def _update_undistorted_image(self, cv_img):
        # Just delegate into camera panel (already subscribed), optional for other overlays
        pass

    def _update_annotated_image(self, cv_img):
        h, w, _ = cv_img.shape
        qimg = QImage(cv_img.data, w, h, 3*w, QImage.Format_RGB888).rgbSwapped()
        self.annotated_label.set_image(qimg)

    def _update_objects(self, msg):
        # Basic textual listing
        lines = [f"{len(msg.objects)} objects"]
        for obj in msg.objects[:10]:  # limit preview
            try:
                oid = getattr(obj, 'id', 'n/a')
                lines.append(f"- id={oid}")
            except Exception:
                lines.append("- <unreadable object>")
        self.objects_content.setText("\n".join(lines))

    def _update_joint_state(self, joint_state):
        # Placeholder: could add a dock with bars later
        pass

    def _simple_cmd_response(self, success, message):
        self.status_simple.setText(f"SimpleCmd: {'OK' if success else 'FAIL'} - {message}")

    def _action_feedback(self, current_state: str):
        """Slot untuk menampilkan feedback dari action server."""
        self.statusBar().showMessage(f"Action Progress: {current_state}")

    def _action_result(self, success: bool, message: str):
        """Slot untuk menampilkan hasil akhir dari action."""
        self.statusBar().showMessage(f"Action Finished: {message}", 5000) # Tampilkan selama 5 detik
        
        # Aktifkan kembali tombol-tombol setelah action selesai
        self.control_panel.analyze_btn.setDisabled(False)
        self.control_panel.send_btn.setDisabled(False)

        if success:
            QMessageBox.information(self, "Action Success", message)
        else:
            QMessageBox.warning(self, "Action Failed / Cancelled", message)

    # ----------------- Button Handlers -----------------
    def _on_simple_command(self):
        # Example: send a dummy move (empty coords allowed per interface)
        self.status_simple.setText("SimpleCmd: sending...")
        self.ros.call_simple_command(coords=[], speed=40, is_linear_mode=True)

    def _on_start_action(self):
        """Mengumpulkan data dari working plane dan memulai action goal."""
        if not self.working_plane.items_on_plane:
            QMessageBox.warning(self, "Error", "No items on the working plane to process.")
            return

        self.statusBar().showMessage("Preparing action goal...")
        
        # Siapkan pesan goal
        objects_to_move = ManyDetectedObjects()
        target_positions = Point2DArray()
        target_orientations = []

        # Kumpulkan data dari setiap item di working plane
        for item in self.working_plane.items_on_plane:
            # Di sini kita asumsikan setiap item adalah target
            # Anda bisa membuat logika lebih canggih untuk membedakan start vs target
            
            # Data objek (menggunakan posisi saat ini sebagai posisi awal)
            start_pos = item.scenePos()
            obj = OneDetectedObject()
            obj.id = item.object_id
            obj.center_point.x = start_pos.x() # Perlu konversi dari pixel/scene ke meter
            obj.center_point.y = start_pos.y() # Perlu konversi dari pixel/scene ke meter
            objects_to_move.objects.append(obj)
            
            # Data target (contoh: pindah 50 unit ke kanan)
            target_pt = Point2D()
            target_pt.x = start_pos.x() + 50.0 # Ganti dengan logika target Anda
            target_pt.y = start_pos.y()
            target_positions.points.append(target_pt)

            # Data orientasi
            target_orientations.append(int(item.rotation()))

        # Kirim goal melalui ROS communication layer
        self.ros_comm.send_complex_goal(objects_to_move, target_positions, target_orientations)
        
        # Nonaktifkan tombol untuk mencegah pengiriman ganda
        self.control_panel.analyze_btn.setDisabled(True)
        self.control_panel.send_btn.setDisabled(True)
        
    def _on_cancel_action(self):
        """Memanggil fungsi cancel di ROS communication layer."""
        self.logger.info("Cancel button clicked.")
        self.ros_comm.cancel_complex_goal()

