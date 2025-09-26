# Standard Python Libraries
import sys
import threading
import cv2
import numpy as np

# Third-Party Libraries
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QTextEdit,
    QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QPushButton, QMainWindow, QDockWidget, QSlider, QDoubleSpinBox, QGraphicsItem, QDialog, QGraphicsEllipseItem
)
from PyQt5.QtGui import QPixmap, QImage, QColor, QBrush, QPen, QPainterPath, QTransform
from PyQt5.QtCore import QTimer, Qt, QRectF, pyqtSignal, QObject, QPointF

# ROS 2 Core Libraries
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from sensor_msgs.msg import Image
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
    def __init__(self, pixmap, original_x, original_y, original_w, original_h):
        super().__init__(pixmap)
        
        self.original_x = original_x
        self.original_y = original_y
        self.original_w = original_w
        self.original_h = original_h
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable
        )
        self.setTransformOriginPoint(self.pixmap().rect().center())
        
        # Add a local transformation to flip the item back vertically
        transform = QTransform()
        transform.scale(1, -1)
        self.setTransform(transform)
        
    def mouseReleaseEvent(self, event):
        # Corrected line to get the center of the pixmap's rectangle
        final_pos = self.mapToScene(self.pixmap().rect().center())
        print(f"Item released at: ({final_pos.x():.1f}, {final_pos.y():.1f}), rotation={self.rotation():.1f}")
        super().mouseReleaseEvent(event)

#========================================================================
class PerspectiveEditorWindow(QDialog):
    def __init__(self, parent, node, frame):
        super().__init__(parent)

        # ----- Setup UI
        self.setWindowTitle("Perspective Editor")
        
        self.node = node
        self.frame = frame
        self.bridge = CvBridge()
        
        # ----- Layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # ----- Left side: graphics scene with originsl image and draggable points
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        main_layout.addWidget(self.view)
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        
        # ----- Default 4 corner points
        self.handles = [
            PointHandle(50, 50),
            PointHandle(w-50, 50),
            PointHandle(w-50, h-50),
            PointHandle(50, h-50)
        ]
        
        for hnd in self.handles:
            self.scene.addItem(hnd)
            
        # ----- Right side: warped preview + button
        side_layout = QVBoxLayout()
        main_layout.addLayout(side_layout)
        
        self.preview_label = QLabel("Warped preview will appear here")
        side_layout.addWidget(self.preview_label)
        
        ok_btn = QPushButton("OK (Send to Detector)")
        ok_btn.clicked.connect(self.on_ok)
        side_layout.addWidget(ok_btn)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_preview_and_publish)
        self.timer.start(200)  # 5 Hz

    def update_preview_and_publish(self):
        pts = np.array([h.get_point() for h in self.handles], dtype=np.float32)

        # Publish Point2DArray
        msg = Point2DArray()
        for (x, y) in pts:
            pt = Point2D()
            pt.x, pt.y = int(x), int(y)
            msg.points.append(pt)
        self.node.pixel_pub.publish(msg)

        # Warp preview
        h, w, _ = self.frame.shape
        dst = np.array([[0,0],[w,0],[w,h],[0,h]], dtype=np.float32)
        M = cv2.getPerspectiveTransform(pts, dst)
        warped = cv2.warpPerspective(self.frame, M, (w,h))

        rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, 3*w, QImage.Format_RGB888)
        self.preview_label.setPixmap(QPixmap.fromImage(qimg))

        self.final_warped = warped
        
        
    def on_ok(self):
        self.node.get_logger().info("Final points confirmed.")
        img_msg = self.bridge.cv2_to_imgmsg(self.final_warped, encoding="bgr8")
        self.node.detector_pub.publish(img_msg)
        self.close()

        

        




#========================================================================

class CombinedROSNode(Node, QObject):   # <-- Node first, then QObject
    refresh_result_signal = pyqtSignal(object)

    def __init__(self, gui_callback, service_callback, node_name='combined_gui_node'):
        Node.__init__(self, node_name)   # initialize ROS2 Node first
        QObject.__init__(self)           # then initialize QObject

        # -------- Initialization --------
        self.bridge = CvBridge()
        self.gui_callback = gui_callback
        self.service_callback = service_callback
        
        # -------- Subscribers ----------
        self.sub_image = self.create_subscription(
            Image, '/vision/msg_undistorted_image', self.image_callback, 10)
        self.sub_objects = self.create_subscription(
            ManyDetectedObjects, 'detected_objects', self.objects_callback, 10)

        # -------- Service client ----------
        self.client = self.create_client(Mycobot280PiSimpleCommandsMadeSure, 'set_coords')
        self.send_coords_request = None
        self.is_service_ready = False

        # -------- Publishers used by the GUI editor ----------
        # GUI will publish Point2DArray points while editing
        self.pixel_pub = self.create_publisher(Point2DArray, 'perspective/points', 10)
        # GUI will publish final warped image to detector input
        self.detector_pub = self.create_publisher(Image, 'detector/input_image', 10)

        # -------- Action client (ProcessWorkspace) ----------
        self.refresh_client = ActionClient(self, ProcessWorkspace, 'refresh_scene')

        # -------- Internal state ----------
        self.latest_frame = None
        self.latest_boxes = []

        # -------- Periodic checks (runs in ROS thread) ----------
        # Keep service-ready flag updated
        self._service_check_timer = self.create_timer(1.0, self.check_service_status)

        self.get_logger().info(f"CombinedROSNode '{node_name}' initialized.")

    # ------------------- ROS Callbacks -------------------
    def image_callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as ex:
            self.get_logger().error(f"Failed to convert incoming image: {ex}")
            return
        self.latest_frame = cv_image
        # gui_callback runs in GUI thread via MainWindow's spin_once QTimer; safe to call
        try:
            self.gui_callback(cv_image, self.latest_boxes)
        except Exception:
            # swallow GUI errors here (GUI owns display)
            pass

    def objects_callback(self, msg: Int32MultiArray):
        data = msg.data
        boxes = []
        for i in range(0, len(data), 4):
            try:
                x, y, w, h = data[i:i+4]
            except Exception:
                break
            boxes.append((x, y, w, h))
        self.latest_boxes = boxes

    # ------------------- Action-related methods -------------------
    def refresh_scene(self):
        """Called from GUI thread (button). Sends a ProcessWorkspace goal to server."""
        if not self.refresh_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warning("ProcessWorkspace action server not available.")
            return

        goal_msg = ProcessWorkspace.Goal()
        send_goal_future = self.refresh_client.send_goal_async(
            goal_msg, feedback_callback=self.refresh_feedback)
        send_goal_future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, fut):
        """Called in ROS thread when goal has been accepted/rejected."""
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
        # feedback_msg is wrapper; print or forward small status if needed
        try:
            fb = feedback_msg.feedback
            # keep lightweight to avoid flooding
            self.get_logger().debug(f"Refresh feedback: {getattr(fb, 'status', '')}")
        except Exception:
            pass

    def refresh_result(self, fut):
        """Result callback (ROS thread). Emit a Qt signal with the cv2 image."""
        try:
            result_wrapper = fut.result()
            result = result_wrapper.result
        except Exception as e:
            self.get_logger().error(f"Failed to get refresh result: {e}")
            return

        if not hasattr(result, 'warped_image') or result.warped_image is None:
            self.get_logger().warn("Refresh result contained no warped_image.")
            return

        try:
            latest_top_down_view = self.bridge.imgmsg_to_cv2(result.warped_image, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Failed to convert result image: {e}")
            return

        # Emit the image to the GUI thread via Qt signal
        # The connected slot (in MainWindow) will run in the GUI thread.
        self.refresh_result_signal.emit(latest_top_down_view)

    # ------------------- Service call helper -------------------
    def call_service(self, req):
        """Call set_coords service asynchronously; GUI provided the done callback."""
        if not self.is_service_ready:
            self.get_logger().warning("Mycobot280PiSimpleCommandsMadeSure service not available.")
            return

        self.send_coords_request = req
        future = self.client.call_async(self.send_coords_request)
        future.add_done_callback(self.service_callback)

    # ------------------- Periodic helpers -------------------
    def check_service_status(self):
        """Toggle is_service_ready based on service availability (runs in ROS thread)."""
        available = self.client.wait_for_service(timeout_sec=0.1)
        if available and not self.is_service_ready:
            self.is_service_ready = True
            self.get_logger().info("Service 'set_coords' is ready.")
        elif not available and self.is_service_ready:
            self.is_service_ready = False
            self.get_logger().info("Service 'set_coords' is not available.")

    # ------------------- Utility (ROS thread -> GUI helper) -------------------
    def update_status_from_ros_thread(self, message):
        """Generic helper to emit a message to GUI (if desired)."""
        self.refresh_result_signal.emit(message)

#========================================================================

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Combined MyCobot GUI")
        self.resize(1200, 800)

        # ------------------- 1. ROS 2 and Data Integration -------------------
        # Note: A separate CombinedROSNode handles all ROS communication.
        # This GUI gets a reference to that node and defines callbacks.
        self.ros_node = CombinedROSNode(
            gui_callback=self.update_gui,
            service_callback=self.on_response_received
        )
        
        self.ros_node.refresh_result_signal.connect(self.handle_refresh_result)


        # Use a QTimer to spin the ROS 2 node, making it non-blocking
        # It calls rclpy.spin_once() at a set interval.
        self.ros_timer = QTimer(self)
        self.ros_timer.timeout.connect(lambda: rclpy.spin_once(self.ros_node, timeout_sec=0))
        self.ros_timer.start(10) # 10 ms interval
        
        # ------------------- 2. Main Layout and UI Elements -------------------
        # Main layout structure (Left, Right, Dock)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_h_layout = QHBoxLayout(central_widget)
        
        # ---- 2a. Left Panel: Camera Feed and Controls
        left_v_layout = QVBoxLayout()
        
        # ---------- welcome text
        self.instruction_text = QTextEdit(
            "Welcome!\n\nCamera feed on the left. Draggable working area on the right. "
            "Use the 'Add Object' button to create new objects on the working plane from the "
            "detected cutouts in the right-side dock panel.\n\n"
            "Select an object on the working plane to see its attributes and send its "
            "pose to the robot. "
        )
        self.instruction_text.setReadOnly(True)
        self.camera_label = QLabel()
        left_v_layout.addWidget(self.instruction_text)
        left_v_layout.addWidget(self.camera_label, 1) # stretch to fill
        
        # ---------- button Refresh Scene
        self.refresh_btn = QPushButton("Refresh Scene")
        self.refresh_btn.clicked.connect(self.ros_node.refresh_scene)
        left_v_layout.addWidget(self.refresh_btn)

        main_h_layout.addLayout(left_v_layout, 1)
        
        
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
        
        self.draw_mycobot280pi_working_plane()
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
        
        controls_h_layout.addWidget(self.reset_btn)
        controls_h_layout.addWidget(self.send_btn)
        controls_h_layout.addWidget(self.add_object_btn)
        
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
        
        # ------------------- 3. ROS2 node GUI Update Callbacks -------------------
        # These methods are triggered by the ROS 2 node to update the UI.
    
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

    def on_response_received(self, future):
        try:
            response = future.result()
            if response.flag:
                print("Service call successful! Coords accepted.")
            else:
                print("Service call failed.")
        except Exception as e:
            print(f"Service call failed with exception: {e}")
            
    # ------------------- 4. Event Handlers & Helper Functions -------------------
    # These methods handle user interaction with the GUI.
  
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

        
    # ------------------- 5. Window Events and Cosmetics -------------------
    # Functions for closing the window and drawing visual elements.

    def closeEvent(self, event):
        # Stop ROS 2 spinning and destroy the node
        self.ros_node.destroy_node()
        rclpy.shutdown()
        event.accept()
        
    def draw_axes_with_ticks(self):    
        # Set up pens for drawing
        pen_axis = QPen(Qt.black, 2)
        pen_ticks = QPen(Qt.black, 1)
    
        # Grid lines (5mm spacing, assuming 1 pixel = 1mm)
        grid_pen = QPen(QColor(200, 200, 200), 1)  # Light gray color for the grid
    
        # Scene boundaries (adjust to your scene's size)
        scene_rect = self.working_plane_scene.sceneRect()
        min_x, max_x = scene_rect.left(), scene_rect.right()
        min_y, max_y = scene_rect.bottom(), scene_rect.top()
    
        # Draw vertical grid lines
        for x in range(int(min_x), int(max_x) + 1, 5):
            self.working_plane_scene.addLine(x, min_y, x, max_y, grid_pen)
        
        # Draw horizontal grid lines
        for y in range(int(min_y), int(max_y) + 1, 5):
            self.working_plane_scene.addLine(min_x, y, max_x, y, grid_pen)

        # Draw the main axes on top of the grid
        self.working_plane_scene.addLine(-280, 0, 280, 0, pen_axis)
        self.working_plane_scene.addLine(0, -280, 0, 280, pen_axis)

        # Draw ticks to match the grid (e.g., every 50mm)
        for x in range(-280, 281, 50):
            if x == 0:
                continue
            length = 12
            self.working_plane_scene.addLine(x, -length / 2, x, length / 2, pen_ticks)
 
        for y in range(-280, 281, 50):
            if y == 0:
                continue
            length = 12
            self.working_plane_scene.addLine(-length / 2, y, length / 2, y, pen_ticks)
         
            
    def draw_mycobot280pi_working_plane(self):
        circle_radius = 280.0
        circle_item = self.working_plane_scene.addEllipse(-circle_radius, -circle_radius, 2 * circle_radius, 2 * circle_radius,
                                          pen=QPen(Qt.NoPen), brush=QBrush(QColor(173, 216, 230, 50)))
        circle_item.setZValue(-1)
        
        rect_width, rect_height, corner_radius = 110, 150, 7.5
        path = QPainterPath()
        path.addRoundedRect(QRectF(-rect_width/2, -rect_height/2, rect_width, rect_height), corner_radius, corner_radius)
        self.working_plane_scene.addPath(path, pen=QPen(Qt.NoPen), brush=QBrush(QColor("#DFDFDF"))).setZValue(0)
        
        robotbase_radius = 45
        self.working_plane_scene.addEllipse(-robotbase_radius, -robotbase_radius, 2*robotbase_radius, 2*robotbase_radius,
                                       pen=QPen(Qt.NoPen), brush=QBrush(QColor("#C3C3C3"))).setZValue(1)
        
        face_width, face_height = 20, 60
        face_item = self.working_plane_scene.addRect(-face_width / 2 - 45, -face_height / 2, face_width, face_height)
        face_item.setPen(QPen(Qt.NoPen))
        face_item.setBrush(QBrush(QColor("#C3C3C3")))
        face_item.setZValue(1)


#========================================================================


def main(args=None):
    rclpy.init(args=args)

    app = QApplication(sys.argv)
    
    # Create the main window instance first
    main_window = MainWindow() 
    
    # Pass the GUI methods to the ROS node here
    gui_node = CombinedROSNode(
        gui_callback=main_window.update_gui,
        service_callback=main_window.on_response_received,
        node_name='action_gui_node'
    )
    
    main_window.show()

    
    try:
        sys.exit(app.exec_())
    finally:
        executor.shutdown()
        gui_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()


