"""grcn_gui_main_window.py

TODO: actually not done yet.

Create instances of your specialized panel widgets (from the other grcn_gui_... files).

Assemble them into the final window layout.

Connect them all so they can talk to each other and to the ROS node.

Hold the high-level application logic that coordinates actions between panels.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDockWidget, QMessageBox, QSizePolicy
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

# from other grcn files
from .grcn_gui_camera_panel import CameraPanel
from .grcn_gui_working_plane import WorkingPlane
from .grcn_gui_control_panel import ControlPanel
from .grcn_gui_dock_panel import DockPanel

# ros interfaces
from mycobot280pi_interfaces.msg import ManyDetectedObjects
from sensor_msgs.msg import Image


class MainWindow(QMainWindow):
    def __init__(self, ros_comm):
        super().__init__()
        self.setWindowTitle("MyCobot 280 Pi GUI")
        self.resize(1400, 900)

        # --- ROS Communication Layer ---
        self.ros_comm = ros_comm
        self.latest_objects_msg = None
        
        # --- Assemble the GUI from Panels ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create instances of all grcn classes 
        self.camera_panel = CameraPanel(self.ros_comm)
        self.working_plane = WorkingPlane()
        self.control_panel = ControlPanel()
        self.dock_panel_widget = DockPanel()
        
        self.items_on_plane = []

        
        
        # --- Assemble the layout ---
        # Right side combines the working plane and its controls
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.working_plane)
        right_layout.addWidget(self.control_panel)

        # Main layout combines the left and right sides
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(self.camera_panel, 1) # Ratio 1
        main_layout.addLayout(right_layout, 2)     # Ratio 2

        # --- Create and set the dock widget ---
        dock = QDockWidget("Controls & Cutouts", self)
        dock.setWidget(self.dock_panel_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
       
        
        # --- Connect Signals and Slots ---
        self.connect_signals()
        
    def connect_signals(self):
        
        # Connect signals from the facade to our handler methods (slots)
        self.ros_comm.detected_objects_received.connect(self.cache_detected_objects)
        self.ros_comm.simple_command_response.connect(self.on_simple_command_response)
        self.ros_comm.action_result.connect(self.on_action_result)
        self.ros_comm.action_feedback.connect(self.on_action_feedback)
        
        # You would also connect signals to your panels here. For example:
        # self.ros_comm.annotated_image_received.connect(self.camera_panel.update_camera_view)
         # --- UNCOMMENT or ADD these lines to connect the buttons ---
        self.control_panel.send_btn.clicked.connect(self.send_service_request)
        self.control_panel.reset_btn.clicked.connect(self.reset_plane)
        self.control_panel.add_object_btn.clicked.connect(self.add_new_objects_from_cutouts)
        self.control_panel.analyze_btn.clicked.connect(self.analyze_positions)
        self.control_panel.delete_btn.clicked.connect(self.delete_selected)
        self.control_panel.rotate_clockwise_btn.clicked.connect(self.working_plane.rotate_clockwise)
        self.control_panel.rotate_counter_clockwise_btn.clicked.connect(self.working_plane.rotate_counter_clockwise)
        
        
    def update_button_states(self, success, message):
        # Example logic, you can tie this to a service availability signal later
        self.control_panel.send_btn.setDisabled(False)
        self.control_panel.analyze_btn.setDisabled(False)

        # You also need to connect the service status to the buttons
        self.ros_comm.simple_command_response.connect(self.update_button_states) # Example
        # A better way would be a dedicated signal for service availability

    # --- Main Application Logic Methods ---
    
    def cache_detected_objects(self, objects_msg: ManyDetectedObjects):
        """Caches the latest message for use by other methods."""
        self.latest_objects_msg = objects_msg
        # You could also forward this signal to the dock panel if it needs it:
        self.dock_panel_widget.update_object_cutouts(objects_msg)
        
        
    def send_service_request(self):
        # This method is now much cleaner! It doesn't need to know about ROS request objects.
        selected_items = self.working_plane.scene.selectedItems()
        if not selected_items:
            print("No item selected.")
            return
        
        item = selected_items[0]
        center_pos = item.mapToScene(item.boundingRect().center())
        rot = item.rotation()

        coords = [center_pos.x(), center_pos.y(), 60.0, 180.0, 0.0, rot]
        
        # Call the clean facade method with simple Python types
        self.ros_comm.call_simple_command(coords=coords, speed=80, is_linear_mode=False) # Example
        print(f"Sent command to robot: x={coords[0]:.1f}, y={coords[1]:.1f}, rz={coords[5]:.1f}")
    
    
    # --- New Slots to handle responses from the facade ---
    def on_simple_command_response(self, success: bool, message: str):
        """Handles the feedback from the simple command service."""
        print(f"Service Response: Success={success}, Message='{message}'")
        # Here you would update a status bar in your GUI.

    def on_action_feedback(self, status: str):
        """Handles live feedback from a running action."""
        print(f"Action Feedback: {status}")
        # Update a status bar with the current action state.

    def on_action_result(self, success: bool, message: str):
        """Handles the final result of an action."""
        print(f"Action Result: Success={success}, Message='{message}'")
        
        
        
        
    
    
        # --- Working Plane Controls ---  
    def reset_plane(self):
        self.working_plane.working_plane_scene.clear()
        self.working_plane.items_on_plane.clear()
        self.working_plane.draw_mycobot280pi_working_plane()
        self.working_plane.draw_axes_with_ticks()
        
    def add_new_objects_from_cutouts(self):
        # We need the last frame and detected boxes to add objects
        if self.latest_objects_msg is None:
            print("No new objects to add (no message received yet).")
            return
            
        try:
            # Get the source image from the cached message
            full_image = self.ros_comm.bridge.imgmsg_to_cv2(self.latest_objects_msg.source_image, 'bgr8')
        except Exception as e:
            print(f"Could not convert source image for cutouts: {e}")
            return

        for obj in self.latest_objects_msg.objects:
            x, y, w, h = obj.box
            if w <= 0 or h <= 0:
                continue

            cutout = full_image[y:y+h, x:x+w]

            # Convert cutout to QPixmap
            rgb = cv2.cvtColor(cutout, cv2.COLOR_BGR2RGB)
            h2, w2, ch = rgb.shape
            bytes_per_line = ch * w2
            qt_img = QImage(rgb.data, w2, h2, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img)

            item = DraggableItem(
                pixmap,
            )
            

            # Make sure these lines are inside this loop
            obj_center_x = x
            obj_center_y = y
            
            # Translate to be relative to the center of the camera frame
            scene_x = obj_center_x - cam_center_x
            scene_y = -(obj_center_y - cam_center_y)
            
            
            # Place new items near the center of the working plane
            item.setPos(scene_x,scene_y)
            self.working_plane.working_plane_scene.addItem(item)
            self.items_on_plane.append(item)
      

    def set_selected_item_rotation(self, angle):
        selected_items = self.working_plane.working_plane_scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            item.setRotation(angle)
    
    def update_rotation_widgets(self):
        selected_items = self.working_plane.working_plane_scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.rotation_slider.setDisabled(False)
            self.rotation_spinbox.setDisabled(False)
            self.rotation_spinbox.setValue(item.rotation())
        else:
            self.rotation_slider.setDisabled(True)
            self.rotation_spinbox.setDisabled(True)
    
    def send_service_request(self):
        selected_items = self.working_plane.working_plane_scene.selectedItems()
        if not selected_items:
            print("No item selected. Cannot send coordinates.")
            return
    
        item = selected_items[0]
        center_pos = item.mapToScene(item.pixmap().rect().center())
        rot = item.rotation()
    
        req = Mycobot280PiSimpleCommandsMadeSure.Request()
        req.x = center_pos.x()
        req.y = center_pos.y()
        req.z = 60.0
        req.rx = 180.0
        req.ry = 0.0
        req.rz = rot
        req.speed = 80
        req.model = 0
    
        self.ros_comm.call_service(req)
        print(f"Sent to robot: x={req.x:.1f}, y={req.y:.1f}, rz={req.rz:.1f}")

    def handle_refresh_result(self, warped_img):
        rgb = cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        self.working_plane.working_plane_scene.clear()
        self.working_plane.working_plane_scene.addPixmap(pixmap)
        
        

   
    def analyze_positions(self):
        print("\n=== Analyzing All Items LOCALLY ===")
        for i, item in enumerate(self.items_on_plane, start=1):
            pos = item.scenePos()
            rot = item.rotation()
            print(f"Item {i}: x={pos.x():.1f}, y={pos.y():.1f}, rotation={rot:.1f}")
        print("==========================\n")

        print("=== Object Analysis ===")
        for i, item in enumerate(self.working_plane.working_plane_scene.items()):
            if isinstance(item, DraggableItem):
                center_in_scene = item.mapToScene(item.rect().center())
                x = center_in_scene.x()
                y = center_in_scene.y()
                rotation = item.rotation()
                print(f"Rect {i+1}: X={x:.2f}, Y={y:.2f}, Rotation={rotation:.2f}°")
        print("=======================")


    def delete_selected(self):
        selected_items = self.working_plane.working_plane_scene.selectedItems()
        for item in selected_items:
            self.working_plane.working_plane_scene.removeItem(item)
            if item in self.items_on_plane:
                self.items_on_plane.remove(item)
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

