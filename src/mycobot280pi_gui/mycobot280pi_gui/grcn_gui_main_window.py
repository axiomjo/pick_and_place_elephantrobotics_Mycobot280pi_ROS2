import cv2 # Make sure cv2 is imported
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

# from other grcn files
from .grcn_gui_camera_panel import CameraPanel
from .grcn_gui_working_plane import WorkingPlane
from .grcn_gui_control_panel import ControlPanel
from .grcn_gui_dock_panel import DockPanel
from .grcn_pyqt_widget import create_cutout_pixmap, DraggableItem

# ros interfaces
from mycobot280pi_interfaces.msg import ManyDetectedObjects

class MainWindow(QMainWindow):
    def __init__(self, ros_comm):
        super().__init__()
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
        
    def connect_signals(self):
        # ROS Facade -> MainWindow Slots
        self.ros_comm.detected_objects_received.connect(self.cache_detected_objects)
        self.ros_comm.annotated_image_received.connect(self.cache_annotated_image)
        self.ros_comm.simple_command_response.connect(self.on_simple_command_response)
        
        # --- BUG FIX: Moved button state connection here ---
        # A better way would be a dedicated signal for service availability
        # self.ros_comm.service_availability.connect(self.update_button_states)
        
        # Control Panel Buttons -> MainWindow Logic
        self.control_panel.send_btn.clicked.connect(self.send_service_request)
        self.control_panel.reset_btn.clicked.connect(self.reset_plane)
        self.control_panel.add_object_btn.clicked.connect(self.add_new_objects_from_cutouts)
        self.control_panel.analyze_btn.clicked.connect(self.analyze_positions)
        self.control_panel.delete_btn.clicked.connect(self.delete_selected)
        
        # --- BUG FIX: Rotation logic is now in WorkingPlane ---
        self.control_panel.rotate_clockwise_btn.clicked.connect(self.working_plane.rotate_clockwise)
        self.control_panel.rotate_counter_clockwise_btn.clicked.connect(self.working_plane.rotate_counter_clockwise)

    # --- Data Caching ---
    def cache_detected_objects(self, objects_msg: ManyDetectedObjects):
        self.latest_objects_msg = objects_msg
        if self.dock_panel_widget and self.latest_annotated_image is not None:
            self.dock_panel_widget.update_object_cutouts(
                self.latest_annotated_image, self.latest_objects_msg)
            
    def cache_annotated_image(self, cv_image):
        self.latest_annotated_image = cv_image
        self.camera_panel.update_camera_view(cv_image)

    # --- High-Level Logic Methods ---
    def reset_plane(self):
        # Now we call a high-level method on the working plane widget
        self.working_plane.reset_scene()

    def add_new_objects_from_cutouts(self):
        if self.latest_objects_msg is None or self.latest_annotated_image is None:
            print("No new objects to add (data not available yet).")
            return
        
        source_image = self.latest_annotated_image
        
        img_height, img_width, _ = source_image.shape
        cam_center_x = img_width / 2.0
        cam_center_y = img_height / 2.0
        
        for obj in self.latest_objects_msg.objects:
            pixmap = create_cutout_pixmap(source_image, obj)
            if pixmap.isNull():
                continue
            item = DraggableItem(pixmap=pixmap, object_id=obj.id)
            
            obj_center_x = obj.center_point.x
            obj_center_y = obj.center_point.y
            scene_x = obj_center_x - cam_center_x
            scene_y = -(obj_center_y - cam_center_y)
            item.setPos(scene_x, scene_y)
            
            # --- BUG FIX: Use the correct scene name ---
            self.working_plane.working_plane_scene.addItem(item)
            self.working_plane.items_on_plane.append(item)
                
        print(f"Added {len(self.latest_objects_msg.objects)} objects to the plane.")
        
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
        print(f"User wants to move the object with ID: {robot_target_id}")
        
        center_pos = item.mapToScene(item.boundingRect().center())
        rot = item.rotation()
        coords = [center_pos.x(), center_pos.y(), 60.0, 180.0, 0.0, rot]
        
        self.ros_comm.call_simple_command(coords=coords, speed=80, is_linear_mode=False)
        print(f"Sent command to robot: x={coords[0]:.1f}, y={coords[1]:.1f}, rz={coords[5]:.1f}")
    
    def on_simple_command_response(self, success: bool, message: str):
        print(f"Service Response: Success={success}, Message='{message}'")
        # Here you would update a status bar or enable/disable buttons.
        self.control_panel.send_btn.setDisabled(False) # Example
        self.control_panel.analyze_btn.setDisabled(False) # Example

    def analyze_positions(self):
        print("\n=== Analyzing All Items on Plane ===")
        # --- BUG FIX: Use the list from the working_plane object ---
        for i, item in enumerate(self.working_plane.items_on_plane, start=1):
            pos = item.scenePos()
            rot = item.rotation()
            print(f"Item {i} (ID: {item.object_id}): x={pos.x():.1f}, y={pos.y():.1f}, rotation={rot:.1f}")
        print("==========================\n")

    def delete_selected(self):
        # --- BUG FIX: Use the correct scene name ---
        selected_items = self.working_plane.working_plane_scene.selectedItems()
        for item in selected_items:
            # --- BUG FIX: Remove from the correct list ---
            self.working_plane.working_plane_scene.removeItem(item)
            if item in self.working_plane.items_on_plane:
                self.working_plane.items_on_plane.remove(item)
        print(f"Deleted {len(selected_items)} item(s).")
      
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
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

    def _action_feedback(self, current_state):
        self.status_action.setText(f"Action: {current_state}")

    def _action_result(self, success, message):
        self.status_action.setText(f"Action: {'SUCCESS' if success else 'FAILED'} - {message}")

    # ----------------- Button Handlers -----------------
    def _on_simple_command(self):
        # Example: send a dummy move (empty coords allowed per interface)
        self.status_simple.setText("SimpleCmd: sending...")
        self.ros.call_simple_command(coords=[], speed=40, is_linear_mode=True)

    def _on_start_action(self):
        self.status_action.setText("Action: sending goal...")
        # Placeholder empty goal components (must conform to interface types)
        from mycobot280pi_interfaces.msg import ManyDetectedObjects, Point2DArray
        empty_objects = ManyDetectedObjects()
        target_positions = Point2DArray()
        target_orientation = []  # list[int]
        self.ros.send_complex_goal(empty_objects, target_positions, target_orientation)

    def _on_cancel_action(self):
        self.ros.cancel_complex_goal()

