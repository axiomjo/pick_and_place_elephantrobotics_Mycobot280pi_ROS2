"""
yg GUI nya bisa muter2.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsItem, QPushButton, QVBoxLayout, QWidget, QMainWindow,
    QDockWidget, QSlider, QDoubleSpinBox, QLabel, QHBoxLayout, QGraphicsEllipseItem
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath, QTransform
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure

# Import the new, non-threaded ROS 2 classes
import rclpy
from .sendcoords_service_client_for_dragndropGUI import SendCoordsServiceClientNode, SendCoordsSignalEmitter


class DraggableItem(QGraphicsRectItem):
    """ A QGraphicsRectItem that can be moved and rotated. """
    def __init__(self, x, y, w, h, color=QColor("skyblue")):
        super().__init__(x, y, w, h)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 2))
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable
        )
        self.setTransformOriginPoint(self.rect().center())

    def mouseReleaseEvent(self, event):
        final_local_pos = self.scenePos()
        print(f"LOCALLY, Item released at: ({final_local_pos.x():.1f}, {final_local_pos.y():.1f}), "
              f"rotation={self.rotation():.1f}")
              
        final_true_pos = self.mapToScene(self.rect().center())
        print(f"Item released at: ({final_true_pos.x():.1f}, {final_true_pos.y():.1f}), "
              f"rotation={self.rotation():.1f}")
        super().mouseReleaseEvent(event)


class GraphicsView(QMainWindow):
    """ Main application window that manages the GUI and communicates with ROS 2. """
    def __init__(self):
        super().__init__()
        
        # --- GUI Setup ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self)
        
        # --- Top POV Controls ---
        self.current_rotation = 0
        top_button_layout = QHBoxLayout()
        self.rotate_counter_clockwise_btn = QPushButton("Rotate 90° Counter-Clockwise")
        self.rotate_clockwise_btn = QPushButton("Rotate 90° Clockwise")
        
        self.rotate_counter_clockwise_btn.clicked.connect(self.rotate_counter_clockwise)
        self.rotate_clockwise_btn.clicked.connect(self.rotate_clockwise)
        
        top_button_layout.addWidget(self.rotate_counter_clockwise_btn)
        top_button_layout.addWidget(self.rotate_clockwise_btn)
        
        
        self.scene.setSceneRect(QRectF(-300, -200, 600, 400))
        self.view.setScene(self.scene)
        self.scene.selectionChanged.connect(self.update_rotation_widgets)
        
        # draw working radius
        self.draw_mycobot280pi_working_plane()
        
        # draw axes and ticks
        self.draw_axes_with_ticks()


        self.items = []
        for i in range(3):
            rect = DraggableItem(50 + i * 120, 80, 80, 80, QColor(100, 150 + i * 40, 200))
            self.scene.addItem(rect)
            self.items.append(rect)

        # Layout for central widget
        main_layout = QVBoxLayout(central_widget)
        main_layout.addLayout(top_button_layout) # Add the new top layout here
        main_layout.addWidget(self.view)
        
        
        
        # --- Side Panel (Dock) ---
        self.dock_panel = QDockWidget("Item Attributes", self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_panel)
        dock_widget_content = QWidget()
        dock_layout = QVBoxLayout(dock_widget_content)
        rotation_label = QLabel("Rotation:")
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
        dock_layout.addWidget(rotation_label)
        dock_layout.addWidget(self.rotation_slider)
        dock_layout.addWidget(self.rotation_spinbox)
        dock_layout.addStretch()
        self.dock_panel.setWidget(dock_widget_content)
        
        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("Analyze (Print All)")
        self.analyze_btn.clicked.connect(self.analyze_positions)
        self.analyze_btn.setDisabled(True)
        button_layout.addWidget(self.analyze_btn)

        self.send_btn = QPushButton("Send to Robot")
        self.send_btn.clicked.connect(self.send_service_request)
        self.send_btn.setDisabled(True)
        button_layout.addWidget(self.send_btn)

        self.add_btn = QPushButton("Add Rectangle")
        self.add_btn.clicked.connect(self.add_rectangle)
        button_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_btn)

        main_layout.addLayout(button_layout)

        # Disable rotation widgets initially
        self.rotation_slider.setDisabled(True)
        self.rotation_spinbox.setDisabled(True)
        
        # --- ROS 2 Integration ---
        self.ros_signal_emitter = SendCoordsSignalEmitter()
        self.ros_client_node = SendCoordsServiceClientNode(self.ros_signal_emitter)

        # Connect signals to the GUI
        self.ros_signal_emitter.service_ready_signal.connect(self.on_service_ready)
        self.ros_signal_emitter.response_received_signal.connect(self.on_response_received)

        # Start the ROS 2 thread (this will init ROS, create node, wait for service, and spin)
        self.ros_client_node.start()
        
        
    def spin_ros_node(self):
        """Spins the ROS node and checks for service status and responses."""
        if rclpy.ok():
            self.ros_client_node.check_service_status()
            self.ros_client_node.check_future()
            

    # ---------- Item Controls ----------
    def set_selected_item_rotation(self, angle):
        selected_items = self.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            item.setRotation(angle % 360)
        
    def update_rotation_widgets(self):
        selected_items = self.scene.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.rotation_slider.setDisabled(False)
            self.rotation_spinbox.setDisabled(False)
            self.rotation_spinbox.setValue(item.rotation())
        else:
            self.rotation_slider.setDisabled(True)
            self.rotation_spinbox.setDisabled(True)

    def add_rectangle(self):
        rect = DraggableItem(100, 100, 80, 80, QColor("orange"))
        self.scene.addItem(rect)
        self.items.append(rect)
        print("Added new rectangle.")

    def delete_selected(self):
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            self.scene.removeItem(item)
            if item in self.items:
                self.items.remove(item)
        print(f"Deleted {len(selected_items)} item(s).")
        
    # --- New POV Methods ---
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
        self.view.setTransform(transform)
        print(f"View rotated to {self.current_rotation % 360}°")
        
    # ---------- Cosmetics ------------
    def draw_axes_with_ticks(self):
        # --- cartesian axes ---
        pen_axis = QPen(Qt.black, 2)
        pen_ticks = QPen(Qt.black, 1)

        # X-axis
        self.scene.addLine(-280, 0, 280, 0, pen_axis)
        # Y-axis
        self.scene.addLine(0, -280, 0, 280, pen_axis)

        # X ticks every 10
        for x in range(-280, 281, 10):
            if x == 0:
                continue
            length = 6 if x % 50 else 12
            self.scene.addLine(x, -length / 2, x, length / 2, pen_ticks)

        # Y ticks every 10
        for y in range(-280, 281, 10):
            if y == 0:
                continue
            length = 6 if y % 50 else 12
            self.scene.addLine(-length / 2, y, length / 2, y, pen_ticks)


    def draw_mycobot280pi_working_plane(self):
        
        #--- working area ----
        circle_radius = 280.0
        circle_item = QGraphicsEllipseItem(-circle_radius, -circle_radius, 2 * circle_radius, 2 * circle_radius)
        
        # Create a QColor with an alpha value (e.g., 150 for semi-transparency)
        semi_transparent_color = QColor(173, 216, 230, 50) # RGBA for lightblue with 150 alpha
        circle_item.setBrush(QBrush(QColor(semi_transparent_color)))
        circle_item.setPen(QPen(Qt.NoPen)) # Use Qt.NoPen for no outline
        circle_item.setZValue(-1) # Place it behind other items
        self.scene.addItem(circle_item)
        
        # --- baseplate ----
        rect_width = 110
        rect_height = 150
        corner_radius =  7.5
        
        rectangle_item = QGraphicsRectItem((-rect_width / 2), (-rect_height / 2), rect_width, rect_height)
        rectangle_item.setRect(QRectF((-rect_width / 2), (-rect_height / 2), rect_width, rect_height))

        path = QPainterPath()
        path.addRoundedRect(QRectF((-rect_width / 2), (-rect_height / 2), rect_width, rect_height), corner_radius, corner_radius)
        
        rounded_rect_item = self.scene.addPath(path)
        rounded_rect_item.setBrush(QBrush(QColor("#DFDFDF")))
        rounded_rect_item.setPen(QPen(Qt.NoPen))
        rounded_rect_item.setZValue(0)
        
        # --- robot base ---
        robotbase_radius = 45
        robotbase_item = QGraphicsEllipseItem(-robotbase_radius, -robotbase_radius, 2 * robotbase_radius, 2 * robotbase_radius)
        
        robotbase_item.setBrush(QBrush(QColor("#C3C3C3")))
        robotbase_item.setPen(QPen(Qt.NoPen))
        robotbase_item.setZValue(1) # Ensure it's on top of the rounded rectangle
        
        self.scene.addItem(robotbase_item)
        
        face_width = 20
        face_height = 60

        face_item = QGraphicsRectItem((-face_width / 2 - 45), (-face_height / 2 ), face_width, face_height)
        
        face_item.setBrush(QBrush(QColor("#C3C3C3")))
        face_item.setPen(QPen(Qt.NoPen))
        face_item.setZValue(1)
        
        self.scene.addItem(face_item)
        
        
        
    # ---------- Analyze & ROS ----------
    def analyze_positions(self):
        print("\n=== Analyzing All Items LOCALLY ===")
        for i, item in enumerate(self.items, start=1):
            pos = item.scenePos()
            rot = item.rotation()
            print(f"Item {i}: x={pos.x():.1f}, y={pos.y():.1f}, rotation={rot:.1f}")
        print("==========================\n")
        
        print("=== Object Analysis ===")
        for i, item in enumerate(self.scene.items()):
            if isinstance(item, DraggableItem):
                # Get the center in scene coordinates
                center_in_scene = item.mapToScene(item.rect().center())
                x = center_in_scene.x()
                y = center_in_scene.y()
                rotation = item.rotation()
                print(f"Rect {i+1}: X={x:.2f}, Y={y:.2f}, Rotation={rotation:.2f}°")
        print("=======================")
    
    def send_service_request(self):
        """Send selected item coords to ROS 2 worker."""
        selected_items = self.scene.selectedItems()
        if not selected_items:
            print("No item selected. Cannot send coordinates.")
            return

        item = selected_items[0]
        center_pos = item.mapToScene(item.rect().center())
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
        
        self.ros_client_node.call_async_service(req)
        print(f"Sent to robot: x={req.x:.1f}, y={req.y:.1f}, rz={req.rz:.1f}")

    # ---------- ROS Feedback ----------
    def on_service_ready(self, is_ready):
        if is_ready:
            self.analyze_btn.setDisabled(False)
            self.send_btn.setDisabled(False)
            print('Service is ready. Buttons enabled.')
        else:
            self.analyze_btn.setDisabled(True)
            self.send_btn.setDisabled(True)
            print('Service not found. Buttons remain disabled.')

    def on_response_received(self, response):
        if response and response.flag:
            print("Service call successful! Coords accepted.")
        else:
            print("Service call failed.")

    def closeEvent(self, event):
        if hasattr(self, "ros_client_node") and self.ros_client_node is not None:
            self.ros_client_node.stop()
        event.accept()


def main():

    # Ensure rclpy is initialized BEFORE any ROS 2 node is created
    app = QApplication(sys.argv)
    win = GraphicsView()
    win.setWindowTitle("Draggable + Rotatable Objects with ROS 2")
    win.resize(900, 600)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
