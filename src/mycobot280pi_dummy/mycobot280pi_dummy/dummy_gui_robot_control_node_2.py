# Standard Python Libraries
import sys
import threading
import cv2
import numpy as np

# Third-Party Libraries
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QTextEdit,
    QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QPushButton, QMainWindow, QDockWidget, QSlider, QDoubleSpinBox, QGraphicsItem, QDialog, QGraphicsEllipseItem, QGraphicsRectItem 
)
from PyQt5.QtGui import QPixmap, QImage, QColor, QBrush, QPen, QPainterPath, QTransform
from PyQt5.QtCore import QTimer, Qt, QRectF, pyqtSignal, QObject, QPointF

# ROS 2 Core Libraries
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from sensor_msgs.msg import Image,JointState
from std_msgs.msg import Int32MultiArray
from cv_bridge import CvBridge

# Custom ROS 2 Interfaces
from mycobot280pi_interfaces.action import ProcessWorkspace
from mycobot280pi_interfaces.msg import Point2DArray, Point2D, ManyDetectedObjects 
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure


#========================================================================

# --- ROS2 Signal Emitter (for thread-safe communication) ---
class SignalEmitter(Node):
    def __init__(self, callback):
        super().__init__('signal_emitter')
        self.timer = self.create_timer(0.1, callback)
        
     
#========================================================================

# ----------- Helper Classes ----------------------
class PointHandle(QGraphicsEllipseItem):
    def __init__(self, x, y, radius=8, color=QColor("red")):
        super().__init__(-radius/2, -radius/2, radius, radius)
        self.setBrush(color)
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsScenePositionChanges, True)
        self.setPos(x, y)

    def get_point(self):
        return int(self.pos().x()), int(self.pos().y())


class DraggableItem(QGraphicsPixmapItem):
    """ A QGraphicsPixmapItem that can be moved and rotated. """
    def __init__(self, pixmap, parent=None):
        super().__init__(pixmap, parent)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable
        )
        # Set transform origin to the center of the pixmap
        self.setTransformOriginPoint(self.boundingRect().center())
        
    def mouseReleaseEvent(self, event):
        final_local_pos = self.scenePos()
        print(f"LOCALLY, Item released at: ({final_local_pos.x():.1f}, {final_local_pos.y():.1f}), "
              f"rotation={self.rotation():.1f}")
              
        final_true_pos = self.mapToScene(self.boundingRect().center())
        print(f"Item released at: ({final_true_pos.x():.1f}, {final_true_pos.y():.1f}), "
              f"rotation={self.rotation():.1f}")
        super().mouseReleaseEvent(event)


#========================================================================

class PerspectiveEditorWidget(QWidget):
    def __init__(self, node, parent=None):
        super().__init__(parent)

        self.node = node
        self.bridge = CvBridge()
        self.frame = None
        self.handles = []
        
        # ----- Layout
        main_layout = QVBoxLayout(self) # Apply layout directly to this widget
        
        # ----- Top: graphics scene
        self.preview_label = QLabel("Warped preview")
        self.perspectivepoints_scene = QGraphicsScene()
        self.view = QGraphicsView(self.perspectivepoints_scene)
        self.pixmap_item = QGraphicsPixmapItem() # Create an empty item to hold the image
        self.perspectivepoints_scene.addItem(self.pixmap_item)
        main_layout.addWidget(self.view)
        
        # ----- Right side: warped preview + button
        ok_btn = QPushButton("Confirm Points")
        ok_btn.clicked.connect(self.on_ok)
        main_layout.addWidget(self.preview_label)
        main_layout.addWidget(ok_btn)

        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_preview_and_publish)
        self.timer.start(200)  # 5 Hz

    def update_frame(self, new_frame):
        """Public method for MainWindow to send new frames to this widget."""
        if new_frame is None:
            return
        self.frame = new_frame
        
        rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        h, w, ch = self.frame.shape
        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item.setPixmap(pixmap)
        
        # Initialize handles only once
        if not self.handles:
            self.handles = [
                PointHandle(50, 50),
                PointHandle(w-50, 50),
                PointHandle(w-50, h-50),
                PointHandle(50, h-50)
            ]
            for hnd in self.handles:
                self.perspectivepoints_scene.addItem(hnd)

    def update_preview_and_publish(self):
        if self.frame is None or not self.handles:
            return

        pts = np.array([h.get_point() for h in self.handles], dtype=np.float32)

        # Publish Point2DArray
        msg = Point2DArray()
        for (x, y) in pts:
            pt = Point2D()
            pt.x, pt.y = int(x), int(y)
            msg.points.append(pt)
            
        self.node.perspective_points_pub.publish(msg) 

        
        
    def on_ok(self):
        # This method can be adapted, perhaps to just log or finalize points
        self.node.get_logger().info("Perspective points confirmed by user.")

     

#========================================================================

class CombinedROSNode(Node, QObject):
    # --- Signals to safely send data from ROS thread to GUI thread ---
    new_undistorted_image_signal = pyqtSignal(object) # For perspective editor
    new_annotated_image_signal = pyqtSignal(object)   # For main camera view
    new_detected_objects_signal = pyqtSignal(object)  # For cutouts and workspace
    new_joint_states_signal = pyqtSignal(object)      # For joint monitoring
    
    # Signal for the action client result
    refresh_result_signal = pyqtSignal(object)

    def __init__(self):
        Node.__init__(self, 'mycobot_gui_controller_node')
        QObject.__init__(self)

        self.bridge = CvBridge()
        self.is_service_ready = False
        self.get_logger().info("GUI ROS 2 Node is running.")

        # === SUBSCRIBERS as per your requirements ===
        self.sub_undistorted_image = self.create_subscription(
            Image, '/vision/msg_undistorted_image', self.undistorted_image_callback, 10)
        
        self.sub_annotated_image = self.create_subscription(
            Image, '/vision/msg_annotated_image', self.annotated_image_callback, 10)
            
        self.sub_objects = self.create_subscription(
            ManyDetectedObjects, '/vision/msg_detected_objects', self.objects_callback, 10)

        self.sub_joint_angles = self.create_subscription(
            JointState, '/robot/msg_joint_angles', self.joint_angles_callback, 10)

        # === PUBLISHER as per your requirements ===
        self.perspective_points_pub = self.create_publisher(
            Point2DArray, '/gui/msg_four_perspective_points', 10)

        # --- Service and Action Clients ---
        self.client = self.create_client(Mycobot280PiSimpleCommandsMadeSure, 'set_coords')
        self.refresh_client = ActionClient(self, ProcessWorkspace, 'refresh_scene')
        self._service_check_timer = self.create_timer(1.0, self.check_service_status)

    # --- Subscriber Callbacks (ROS Thread) ---
    def undistorted_image_callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.new_undistorted_image_signal.emit(cv_image)
        except Exception as e:
            self.get_logger().error(f"Failed to convert undistorted image: {e}")

    def annotated_image_callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.new_annotated_image_signal.emit(cv_image)
        except Exception as e:
            self.get_logger().error(f"Failed to convert annotated image: {e}")

    def objects_callback(self, msg: ManyDetectedObjects):
        # The message is already the correct type, just emit it
        self.new_detected_objects_signal.emit(msg)

    def joint_angles_callback(self, msg: JointState):
        self.new_joint_states_signal.emit(msg)
    
    # --- Service call helper (called by GUI) ---
    def call_service(self, req, service_callback):
        if not self.is_service_ready:
            self.get_logger().warning("Mycobot service not available.")
            return
        future = self.client.call_async(req)
        future.add_done_callback(service_callback)

    # ... (rest of the Action Client and periodic helper methods remain the same) ...
    # ------------------- Action-related methods -------------------
    def refresh_scene(self):
        if not self.refresh_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warning("ProcessWorkspace action server not available.")
            return
        goal_msg = ProcessWorkspace.Goal()
        send_goal_future = self.refresh_client.send_goal_async(goal_msg, feedback_callback=self.refresh_feedback)
        send_goal_future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, fut):
        try:
            goal_handle = fut.result()
        except Exception as e:
            self.get_logger().error(f"Send goal failed: {e}")
            return
        if not goal_handle.accepted:
            self.get_logger().info("ProcessWorkspace goal rejected by server.")
            return
        self.get_logger().info("ProcessWorkspace goal accepted; waiting for result...")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.refresh_result)

    def refresh_feedback(self, feedback_msg):
        self.get_logger().debug(f"Refresh feedback: {getattr(feedback_msg.feedback, 'status', '')}")

    def refresh_result(self, fut):
        try:
            result = fut.result().result
        except Exception as e:
            self.get_logger().error(f"Failed to get refresh result: {e}")
            return
        if not hasattr(result, 'warped_image') or result.warped_image is None:
            self.get_logger().warn("Refresh result contained no warped_image.")
            return
        try:
            latest_top_down_view = self.bridge.imgmsg_to_cv2(result.warped_image, desired_encoding='bgr8')
            self.refresh_result_signal.emit(latest_top_down_view)
        except Exception as e:
            self.get_logger().error(f"Failed to convert result image: {e}")

    # ------------------- Periodic helpers -------------------
    def check_service_status(self):
        available = self.client.wait_for_service(timeout_sec=0.1)
        if available != self.is_service_ready:
            self.is_service_ready = available
            self.get_logger().info(f"Service 'set_coords' is now {'available' if available else 'unavailable'}.")        




#========================================================================

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self, ros_node):
        super().__init__()
        self.setWindowTitle("myCobot 280Pi Control GUI")
        self.resize(1400, 900)
        self.ros_node = ros_node # Store the passed-in ROS node

        
        # ------------------- 2. Main Layout and UI Elements -------------------
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_h_layout = QHBoxLayout(central_widget)

         # ---- 2a. Left Panel: Camera, Perspective Editor, and Joint Info
        left_v_layout = QVBoxLayout()

        # Annotated camera view
        self.camera_label = QLabel("Waiting for annotated camera feed...")
        self.camera_label.setMinimumHeight(300)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("border: 1px solid black;")
        left_v_layout.addWidget(self.camera_label)

        # Embedded perspective editor
        self.perspective_editor = PerspectiveEditorWidget(node=self.ros_node, parent=self)
        left_v_layout.addWidget(self.perspective_editor)

        # Joint states display
        self.joint_states_label = QTextEdit("Waiting for joint states...")
        self.joint_states_label.setReadOnly(True)
        self.joint_states_label.setMaximumHeight(150)
        left_v_layout.addWidget(self.joint_states_label)

        main_h_layout.addLayout(left_v_layout, 1) # Left panel takes 1/3 space

        
        # ---- 2b. Right Panel: Working Plane and Controls
        right_v_layout = QVBoxLayout()
        
        # ---------- Graphics View for the main working plane
        self.working_plane_view = QGraphicsView()
        self.working_plane_scene = QGraphicsScene(self)
        self.working_plane_scene.setSceneRect(QRectF(-300, -300, 600, 600))
        self.working_plane_view.setScene(self.working_plane_scene)
        
        self.working_plane_scene.selectionChanged.connect(self.update_rotation_widgets)
        
        transform = QTransform()
        transform.scale(1, -1)
        self.working_plane_view.setTransform(transform)
        
        
        # draw working radius
        self.draw_mycobot280pi_working_plane()
        
        # draw axes and ticks
        self.draw_axes_with_ticks()

        self.items_on_plane = []
        
        right_v_layout.addWidget(self.working_plane_view, 2)
        
        # ---------- Control buttons for the working plane
        controls_h_layout = QHBoxLayout()
        
        self.send_btn = QPushButton("Send to Robot")
        self.send_btn.setDisabled(True)
        self.send_btn.clicked.connect(self.send_service_request)
        
        self.add_object_btn = QPushButton("Add New Object (to Plane)")
        self.add_object_btn.clicked.connect(self.add_new_objects_from_cutouts)
        
        self.reset_btn = QPushButton("Reset Plane")
        self.reset_btn.clicked.connect(self.reset_plane)
        
        
        self.current_rotation = 0
        
        self.rotate_counter_clockwise_btn = QPushButton("Rotate 90° Counter-Clockwise")
        self.rotate_counter_clockwise_btn.clicked.connect(self.rotate_counter_clockwise)
        
        self.rotate_clockwise_btn = QPushButton("Rotate Clockwise")
        self.rotate_clockwise_btn.clicked.connect(self.rotate_clockwise)


       
        controls_h_layout.addWidget(self.reset_btn)
        controls_h_layout.addWidget(self.send_btn)
        controls_h_layout.addWidget(self.add_object_btn)
        controls_h_layout.addWidget(self.rotate_counter_clockwise_btn)
        controls_h_layout.addWidget(self.rotate_clockwise_btn)
        
        right_v_layout.addLayout(controls_h_layout)

        main_h_layout.addLayout(right_v_layout, 2)
        
        
        # ---- 2c. Dock Widget for Object Cutouts and Rotation Controls
        self.dock_panel = QDockWidget("Object Cutouts & Controls", self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_panel)
        dock_widget_content = QWidget()
        dock_v_layout = QVBoxLayout(dock_widget_content)
        
        # ---------- Cutout View
        self.cutout_scene = QGraphicsScene()
        self.cutout_view = QGraphicsView(self.cutout_scene)
        self.cutout_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cutout_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        dock_v_layout.addWidget(QLabel("Detected Object Cutouts:"))
        dock_v_layout.addWidget(self.cutout_view)
        
        # ---------- Rotation Controls
        rotation_label = QLabel("Rotation (Selected Object):")
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)
        self.rotation_spinbox = QDoubleSpinBox()
        self.rotation_spinbox.setRange(-180, 180)
        self.rotation_spinbox.setSingleStep(0.1)
        self.rotation_spinbox.setDecimals(1)
        self.rotation_slider.valueChanged.connect(self.rotation_spinbox.setValue)
        self.rotation_spinbox.valueChanged.connect(self.rotation_slider.setValue)
        self.rotation_spinbox.valueChanged.connect(self.set_selected_item_rotation)
        
        dock_v_layout.addWidget(rotation_label)
        dock_v_layout.addWidget(self.rotation_slider)
        dock_v_layout.addWidget(self.rotation_spinbox)
        self.rotation_slider.setDisabled(True)
        self.rotation_spinbox.setDisabled(True)
        
        dock_widget_content.setLayout(dock_v_layout)
        self.dock_panel.setWidget(dock_widget_content)
        
        
        # ------------------- 3. Connect ROS Node Signals to GUI Slots -------------------
        self.ros_node.new_undistorted_image_signal.connect(self.perspective_editor.update_frame)
        self.ros_node.new_annotated_image_signal.connect(self.update_camera_view)
        self.ros_node.new_detected_objects_signal.connect(self.update_object_cutouts)
        self.ros_node.new_joint_states_signal.connect(self.update_joint_display)
        self.ros_node.refresh_result_signal.connect(self.handle_refresh_result)


    # ------------------- 4. GUI Update Slots (called by ROS signals) -------------------
    def update_camera_view(self, cv_image):
        """Displays the annotated image."""
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.camera_label.setPixmap(pixmap.scaled(
            self.camera_label.width(), self.camera_label.height(), Qt.KeepAspectRatio))

    def update_object_cutouts(self, objects_msg: ManyDetectedObjects):
        """Clears and repopulates the cutout view from detected objects."""
        # You will need to implement the logic here based on your ManyDetectedObjects msg
        # For example, if it contains bounding boxes and an image:
        # self.cutout_scene.clear()
        # y_offset = 0
        # for obj in objects_msg.objects:
        #   x, y, w, h = obj.box
        #   # create pixmap and add to cutout_scene...
        #   y_offset += 110
        pass # Placeholder for your cutout logic

    def update_joint_display(self, joint_state_msg: JointState):
        """Displays the latest joint states."""
        text = "Joint States:\n"
        for i, name in enumerate(joint_state_msg.name):
            angle_deg = np.rad2deg(joint_state_msg.position[i])
            text += f"- {name}: {angle_deg:.2f}°\n"
        self.joint_states_label.setText(text)

    def on_response_received(self, future):
        # This is the callback for the service client
        try:
            response = future.result()
            print(f"Service call successful: {response.flag}")
        except Exception as e:
            print(f"Service call failed with exception: {e}")
    
    def update_gui(self, image, boxes):
        """Callback from ROS node to update the GUI with image data."""
        # Update camera feed
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.camera_label.setPixmap(pixmap.scaled(self.camera_label.width(), self.camera_label.height(), Qt.KeepAspectRatio))

        # Update service button state
        self.send_btn.setDisabled(not self.ros_node.is_service_ready)

        # Clear and update cutout scene
        self.cutout_scene.clear()
        x_offset = 0
        y_offset = 0
        for (x, y, w, h) in boxes:
            if w <= 0 or h <= 0:
                continue
            cutout = image[y:y+h, x:x+w].copy()
            if cutout.size == 0:
                continue

            rgb_cutout = cv2.cvtColor(cutout, cv2.COLOR_BGR2RGB)
            h_c, w_c, ch_c = rgb_cutout.shape
            bytes_per_line_c = ch_c * w_c
            qt_img_c = QImage(rgb_cutout.data, w_c, h_c, bytes_per_line_c, QImage.Format_RGB888)
            pixmap_c = QPixmap.fromImage(qt_img_c)
            
            # Use a non-draggable, simple PixmapItem for the cutout view
            item = QGraphicsPixmapItem(pixmap_c.scaled(100, 100, Qt.KeepAspectRatio))
            item.setPos(x_offset, y_offset)
            self.cutout_scene.addItem(item)
            y_offset += 110 # Space out cutouts vertically

       
    # ------------------- 4. Event Handlers & Helper Functions -------------------
    # These methods handle user interaction with the GUI.
    
    def open_perspective_editor(self):
        """Creates and shows the PerspectiveEditorWindow dialog."""
        # Make sure we have a camera frame to work with
        if self.ros_node.latest_frame is None:
            print("Cannot open perspective editor: No camera image received yet.")
            return

        # Create an instance of the editor window
        editor_dialog = PerspectiveEditorWindow(
            parent=self, 
            node=self.ros_node, 
            frame=self.ros_node.latest_frame
        )
        # Execute the dialog (this will show the window and pause the main window)
        editor_dialog.exec_()

    
    # --- Working Plane Controls ---  
    def reset_plane(self):
        self.working_plane_scene.clear()
        self.items_on_plane.clear()
        self.draw_mycobot280pi_working_plane()
        self.draw_axes_with_ticks()
        
    def add_new_objects_from_cutouts(self):
        # We need the last frame and detected boxes to add objects
        frame = self.ros_node.latest_frame
        boxes = self.ros_node.latest_boxes
        
        if frame is None or not boxes:
            print("No new objects to add.")
            return
            
        # Get the camera's center
        height, width, _ = frame.shape
        cam_center_x = width / 2.0
        cam_center_y = height / 2.0

        for (x, y, w, h) in boxes:
            if w <= 0 or h <= 0:
                continue

            cutout = frame[y:y+h, x:x+w].copy()
            if cutout.size == 0:
                continue

            rgb = cv2.cvtColor(cutout, cv2.COLOR_BGR2RGB)
            h2, w2, ch = rgb.shape
            bytes_per_line = ch * w2
            qt_img = QImage(rgb.data, w2, h2, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img)

            item = DraggableItem(
                pixmap,
                original_x=x,
                original_y=y,
                original_w=w,
                original_h=h
            )
            

            # Make sure these lines are inside this loop
            obj_center_x = x
            obj_center_y = y
            
            # Translate to be relative to the center of the camera frame
            scene_x = obj_center_x - cam_center_x
            scene_y = -(obj_center_y - cam_center_y)
            
            
            # Place new items near the center of the working plane
            item.setPos(scene_x,scene_y)
            self.working_plane_scene.addItem(item)
            self.items_on_plane.append(item)
      

    def set_selected_item_rotation(self, angle):
        selected_items = self.working_plane_scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            item.setRotation(angle)
    
    def update_rotation_widgets(self):
        selected_items = self.working_plane_scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.rotation_slider.setDisabled(False)
            self.rotation_spinbox.setDisabled(False)
            self.rotation_spinbox.setValue(item.rotation())
        else:
            self.rotation_slider.setDisabled(True)
            self.rotation_spinbox.setDisabled(True)
    
    def send_service_request(self):
        selected_items = self.working_plane_scene.selectedItems()
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
    
        self.ros_node.call_service(req)
        print(f"Sent to robot: x={req.x:.1f}, y={req.y:.1f}, rz={req.rz:.1f}")

    def handle_refresh_result(self, warped_img):
        rgb = cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        self.working_plane_scene.clear()
        self.working_plane_scene.addPixmap(pixmap)

    def rotate_clockwise(self):
        self.current_rotation -= 90
        self.set_pov()

    def rotate_counter_clockwise(self):
        self.current_rotation += 90
        self.set_pov()

    def set_pov(self):
        transform = QTransform()
        transform.scale(1, -1)
        transform.rotate(self.current_rotation)
        self.working_plane_view.setTransform(transform)
        print(f"View rotated to {self.current_rotation % 360}°")

    def analyze_positions(self):
        print("\n=== Analyzing All Items LOCALLY ===")
        for i, item in enumerate(self.items_on_plane, start=1):
            pos = item.scenePos()
            rot = item.rotation()
            print(f"Item {i}: x={pos.x():.1f}, y={pos.y():.1f}, rotation={rot:.1f}")
        print("==========================\n")

        print("=== Object Analysis ===")
        for i, item in enumerate(self.working_plane_scene.items()):
            if isinstance(item, DraggableItem):
                center_in_scene = item.mapToScene(item.rect().center())
                x = center_in_scene.x()
                y = center_in_scene.y()
                rotation = item.rotation()
                print(f"Rect {i+1}: X={x:.2f}, Y={y:.2f}, Rotation={rotation:.2f}°")
        print("=======================")

    # Add buttons for analyze and delete
    def setup_control_buttons(self):
        # ...existing code...
        self.analyze_btn = QPushButton("Analyze (Print All)")
        self.analyze_btn.clicked.connect(self.analyze_positions)
        self.analyze_btn.setDisabled(True)
        controls_h_layout.addWidget(self.analyze_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        controls_h_layout.addWidget(self.delete_btn)

    def delete_selected(self):
        selected_items = self.working_plane_scene.selectedItems()
        for item in selected_items:
            self.working_plane_scene.removeItem(item)
            if item in self.items_on_plane:
                self.items_on_plane.remove(item)
        print(f"Deleted {len(selected_items)} item(s).")
    
    def draw_axes_with_ticks(self):
        # --- cartesian axes ---
        pen_axis = QPen(Qt.black, 2)
        pen_ticks = QPen(Qt.black, 1)

        # X-axis
        self.working_plane_scene.addLine(-280, 0, 280, 0, pen_axis)
        # Y-axis
        self.working_plane_scene.addLine(0, -280, 0, 280, pen_axis)

        # X ticks every 10
        for x in range(-280, 281, 10):
            if x == 0:
                continue
            length = 6 if x % 50 else 12
            self.working_plane_scene.addLine(x, -length / 2, x, length / 2, pen_ticks)

        # Y ticks every 10
        for y in range(-280, 281, 10):
            if y == 0:
                continue
            length = 6 if y % 50 else 12
            self.working_plane_scene.addLine(-length / 2, y, length / 2, y, pen_ticks)

        
    def draw_mycobot280pi_working_plane(self):
        
        #--- working area ----
        circle_radius = 280.0
        circle_item = QGraphicsEllipseItem(-circle_radius, -circle_radius, 2 * circle_radius, 2 * circle_radius)
        
        # Create a QColor with an alpha value (e.g., 150 for semi-transparency)
        semi_transparent_color = QColor(173, 216, 230, 50) # RGBA for lightblue with 150 alpha
        circle_item.setBrush(QBrush(QColor(semi_transparent_color)))
        circle_item.setPen(QPen(Qt.NoPen)) # Use Qt.NoPen for no outline
        circle_item.setZValue(-1) # Place it behind other items
        self.working_plane_scene.addItem(circle_item)
        
        # --- baseplate ----
        rect_width = 110
        rect_height = 150
        corner_radius =  7.5
        
        rectangle_item = QGraphicsRectItem((-rect_width / 2), (-rect_height / 2), rect_width, rect_height)
        rectangle_item.setRect(QRectF((-rect_width / 2), (-rect_height / 2), rect_width, rect_height))

        path = QPainterPath()
        path.addRoundedRect(QRectF((-rect_width / 2), (-rect_height / 2), rect_width, rect_height), corner_radius, corner_radius)
        
        rounded_rect_item = self.working_plane_scene.addPath(path)
        rounded_rect_item.setBrush(QBrush(QColor("#DFDFDF")))
        rounded_rect_item.setPen(QPen(Qt.NoPen))
        rounded_rect_item.setZValue(0)
        
        # --- robot base ---
        robotbase_radius = 45
        robotbase_item = QGraphicsEllipseItem(-robotbase_radius, -robotbase_radius, 2 * robotbase_radius, 2 * robotbase_radius)
        
        robotbase_item.setBrush(QBrush(QColor("#C3C3C3")))
        robotbase_item.setPen(QPen(Qt.NoPen))
        robotbase_item.setZValue(1) # Ensure it's on top of the rounded rectangle
        
        self.working_plane_scene.addItem(robotbase_item)
        
        face_width = 20
        face_height = 60

        face_item = QGraphicsRectItem((-face_width / 2 - 45), (-face_height / 2 ), face_width, face_height)
        
        face_item.setBrush(QBrush(QColor("#C3C3C3")))
        face_item.setPen(QPen(Qt.NoPen))
        face_item.setZValue(1)
        
        self.working_plane_scene.addItem(face_item)
        
        
 

# ...existing code...


def main(args=None):
    rclpy.init(args=args)
    
    # --- Standard ROS2 + PyQt5 integration ---
    app = QApplication(sys.argv)
    
    # 1. Create the ROS 2 node
    ros_node = CombinedROSNode()
    
    # 2. Create the GUI, passing the node to it
    main_window = MainWindow(ros_node)
    main_window.show()
    
    # 3. Set up a ROS 2 executor in a separate thread
    executor = MultiThreadedExecutor()
    executor.add_node(ros_node)
    
    # 4. Start the ROS 2 thread
    ros_thread = threading.Thread(target=executor.spin)
    ros_thread.daemon = True
    ros_thread.start()

    try:
        # Start the Qt event loop (this blocks)
        sys.exit(app.exec_())
    finally:
        # Cleanup
        print("Shutting down ROS 2 node...")
        executor.shutdown()
        ros_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()


