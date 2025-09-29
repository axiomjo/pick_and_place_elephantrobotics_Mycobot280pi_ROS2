import cv2 # Make sure cv2 is imported
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget, QMessageBox
from PyQt5.QtGui import QImage, QPixmap, QTransform
from PyQt5.QtCore import Qt
from enum import Enum # <<< ADDED: Import Enum for state machine

# from other grcn files
from .grcn_gui_camera_panel import CameraPanel
from .grcn_gui_working_plane import WorkingPlane
from .grcn_gui_control_panel import ControlPanel
from .grcn_gui_dock_panel import DockPanel
from .grcn_pyqt_widget import create_cutout_pixmap, DraggableItem

from mycobot280pi_interfaces.msg import OneDetectedObject, ManyDetectedObjects, Point2DArray, Point2D # Impor pesan yang dibutuhkan

class MainWindow(QMainWindow):
    # <<< ADDED: State machine definition
    AppState = Enum('AppState', ['IDLE', 'BUSY', 'FINISHED'])
    
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
        
        # <<< MODIFIED: Initialize the state machine
        self._set_state(self.AppState.IDLE) 
        self.statusBar().showMessage("GUI is Ready.")
        
    def connect_signals(self):
        # ROS Facade -> MainWindow Slots
        self.ros_comm.detected_objects_received.connect(self.cache_detected_objects)
        self.ros_comm.annotated_image_received.connect(self.cache_annotated_image)
        self.ros_comm.simple_command_response.connect(self.on_simple_command_response)
        
        self.ros_comm.action_feedback.connect(self._action_feedback)
        self.ros_comm.action_result.connect(self._action_result)
        
        # Control Panel Buttons -> MainWindow Logic
        self.control_panel.analyze_btn.clicked.connect(self._on_start_action) # This is the PnP button
        self.control_panel.emergency_btn.clicked.connect(self._on_cancel_action)
        self.control_panel.send_btn.clicked.connect(self.send_service_request)
        self.control_panel.reset_btn.clicked.connect(self.reset_plane)
        self.control_panel.add_object_btn.clicked.connect(self.add_new_objects_from_cutouts)
        self.control_panel.delete_btn.clicked.connect(self.delete_selected)
        
        self.dock_panel_widget.rotation_slider.valueChanged.connect(self.working_plane.set_selected_items_rotation)
        
        self.working_plane.working_plane_scene.selectionChanged.connect(self.update_status_bar_with_selection)
        
        # Rotation buttons
        self.control_panel.rotate_clockwise_btn.clicked.connect(self.working_plane.rotate_clockwise)
        self.control_panel.rotate_counter_clockwise_btn.clicked.connect(self.working_plane.rotate_counter_clockwise)

    # <<< ADDED: Central state management function
    def _set_state(self, new_state: AppState):
        """Manages the UI based on the application state."""
        self.state = new_state
        self.logger.info(f"--- Application state changed to: {self.state.name} ---")

        # By default, most controls are enabled in IDLE/FINISHED and disabled in BUSY
        is_busy = (self.state == self.AppState.BUSY)
        self.control_panel.add_object_btn.setDisabled(is_busy)
        self.control_panel.delete_btn.setDisabled(is_busy)
        self.control_panel.reset_btn.setDisabled(is_busy)
        self.control_panel.rotate_clockwise_btn.setDisabled(is_busy)
        self.control_panel.rotate_counter_clockwise_btn.setDisabled(is_busy)

        # Handle specific logic for each state
        if self.state == self.AppState.IDLE:
            # Ready to start a new plan
            self.control_panel.analyze_btn.setEnabled(True)  # PnP button is enabled
            self.control_panel.emergency_btn.setEnabled(False) # Cancel button is disabled

        elif self.state == self.AppState.BUSY:
            # Action is running, only cancel is allowed
            self.control_panel.analyze_btn.setEnabled(False)
            self.control_panel.emergency_btn.setEnabled(True)

        elif self.state == self.AppState.FINISHED:
            # Action is done, must reset to continue
            self.control_panel.analyze_btn.setEnabled(False) # PnP button is DISABLED
            self.control_panel.emergency_btn.setEnabled(False)
            self.control_panel.reset_btn.setEnabled(True) # Only Reset is enabled

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
        self.working_plane.reset_scene()
        # <<< MODIFIED: Transition back to IDLE state after reset
        self._set_state(self.AppState.IDLE)
        self.statusBar().showMessage("Plane has been reset. Ready for new plan.")


    def add_new_objects_from_cutouts(self):
        if self.state != self.AppState.IDLE:
            self.statusBar().showMessage("Cannot add objects while an action is running or finished.", 3000)
            return

        objects_to_process = self.latest_objects_msg
        image_to_process = self.latest_annotated_image
        
        if self.latest_objects_msg is None or self.latest_annotated_image is None:
            self.logger.warn("Add objects called, but data is not ready yet.")
            self.statusBar().showMessage("Data not available to add objects.")
            return

        img_height, img_width, _ = image_to_process.shape
        cam_center_x = img_width / 2.0
        cam_center_y = img_height / 2.0
        
        current_object_count = len(self.working_plane.items_on_plane)

        for obj in self.latest_objects_msg.objects:
            try:
                self.logger.info(f"--- Processing Object ID {obj.id} ---")

                pixmap = create_cutout_pixmap(image_to_process, obj)
                if pixmap.isNull(): continue
                
                transform = QTransform()
                transform.scale(1, -1)
                flipped_pixmap = pixmap.transformed(transform)
                if flipped_pixmap.isNull(): continue
                
                item = DraggableItem(pixmap=flipped_pixmap, detected_object=obj)
                
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
                error_msg = f"ERROR on obj {obj.id}: {type(e).__name__}. See terminal."
                self.statusBar().showMessage(error_msg, 5000)
                
                self.logger.error("\n" + "="*20)
                self.logger.error(f"CAUGHT EXCEPTION: {type(e).__name__} - {e}")
                self.logger.error(f"Problem occurred on Object ID: {obj.id}")
                self.logger.error("--- Dumping Problematic Object Data ---")
                self.logger.error(f"{obj}")
                self.logger.error("="*20 + "\n")

        new_items_count = len(self.working_plane.items_on_plane) - current_object_count
        self.statusBar().showMessage(f"Added {new_items_count} new objects to the plane.")
        
    def send_service_request(self):
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
        # The state machine now handles button enabling/disabling
        pass

    def analyze_positions(self):
        for i, item in enumerate(self.working_plane.items_on_plane, start=1):
            pos = item.scenePos()
            rot = item.rotation()

    def update_status_bar_with_selection(self):
        """
        Called whenever the selection changes. Updates the status bar AND
        tells the DockPanel to update its rotation controls.
        """
        selected_items = self.working_plane.working_plane_scene.selectedItems()

        if not selected_items:
            self.statusBar().showMessage("No item selected.")
            # Tell the dock panel that nothing is selected
            self.dock_panel_widget.update_rotation_widgets(is_item_selected=False)
            return

        # If we get here, at least one item is selected
        item = selected_items[0]

        if isinstance(item, DraggableItem):
            pos = item.mapToScene(item.boundingRect().center())
            rot = item.rotation()

            # Update the status bar
            message = (
                f"Selected Item ID: {item.object_id} | "
                f"Position: (X={pos.x():.1f}, Y={pos.y():.1f}) | "
                f"Rotation: {rot:.1f}°"
            )
            self.statusBar().showMessage(message)

            # Tell the dock panel an item IS selected and what its rotation is
            self.dock_panel_widget.update_rotation_widgets(
                is_item_selected=True, 
                rotation_value=rot
            )
    def delete_selected(self):
        selected_items = self.working_plane.working_plane_scene.selectedItems()
        for item in selected_items:
            self.working_plane.working_plane_scene.removeItem(item)
            if item in self.working_plane.items_on_plane:
                self.working_plane.items_on_plane.remove(item)

    # ----------------- GUI Slots -----------------
    def _action_feedback(self, current_state: str):
        self.statusBar().showMessage(f"Action Progress: {current_state}")

    def _action_result(self, success: bool, message: str):
        self.statusBar().showMessage(f"Action Finished: {message}", 5000)
        
        # <<< MODIFIED: Transition to FINISHED state
        self._set_state(self.AppState.FINISHED)
        # Old button logic is removed from here

        if success:
            QMessageBox.information(self, "Action Success", message)
        else:
            QMessageBox.warning(self, "Action Failed / Cancelled", message)

    # ----------------- Button Handlers -----------------
    def _on_start_action(self):
        moved_items = [item for item in self.working_plane.items_on_plane if item.was_moved]
        
        if not moved_items:
            QMessageBox.warning(self, "Error", "No items have been moved to a new target position.")
            return

        self.statusBar().showMessage("Preparing action goal for moved items...")
        
        objects_to_move = ManyDetectedObjects()
        target_positions = Point2DArray()
        target_orientations = []

        for item in moved_items:
            original_object_data = item.detected_object
            objects_to_move.objects.append(original_object_data)
            
            new_pos_scene = item.scenePos()
            target_pt = Point2D()
            target_pt.x = new_pos_scene.x()
            target_pt.y = new_pos_scene.y()
            target_positions.points.append(target_pt)

            target_orientations.append(int(item.rotation()))

        self.ros_comm.send_complex_goal(objects_to_move, target_positions, target_orientations)
        
        # <<< MODIFIED: Transition to BUSY state
        self._set_state(self.AppState.BUSY)

    def _on_cancel_action(self):
        self.logger.info("Cancel button clicked.")
        self.ros_comm.cancel_complex_goal()
