import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QSlider, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLineEdit
)
from PyQt5.QtCore import Qt

import rclpy
from rclpy.node import Node
from mycobot_interfaces.msg import MycobotCoords
from sensor_msgs.msg import JointState


class MyCobotGUI(Node, QWidget):
    def __init__(self):
        Node.__init__(self, 'gui_node')
        QWidget.__init__(self)
        self.setWindowTitle("MyCobot GUI Controller 29jul")

        # ROS Publisher & Subscriber
        self.pose_pub = self.create_publisher(MycobotCoords, 'mycobot_280pi_29jul/pose_goal', 10)
        self.joint_sub = self.create_subscription(JointState, 'joint_states', self.joint_callback, 10)

        self.joint_labels = []
        self.slider_labels = []
        self.sliders = []
        
        self.coord_configs = [
            {'name': 'x',  'min_val': -280, 'max_val': 280, 'scale_factor': 100},
            {'name': 'y',  'min_val': -280, 'max_val': 280, 'scale_factor': 100},
            {'name': 'z',  'min_val': -70.0,   'max_val': 412, 'scale_factor': 100},
            {'name': 'rx', 'min_val': -180.0,  'max_val': 180.0,  'scale_factor': 10},
            {'name': 'ry', 'min_val': -180.0,  'max_val': 180.0,  'scale_factor': 10},
            {'name': 'rz', 'min_val': -180.0,  'max_val': 180.0,  'scale_factor': 10}
        ]
        # We'll use these to get the initial values later
        self.slider_values = [config['min_val'] for config in self.coord_configs] # Initialize with min values


        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # GroupBox for sliders
        slider_group = QGroupBox("Target Pose Input (x, y, z, rx, ry, rz)")
        grid = QGridLayout()


        for i, config in enumerate(self.coord_configs):
            name = config['name']
            min_float = config['min_val']
            max_float = config['max_val']
            scale = config['scale_factor']

            # Calculate integer min/max for the QSlider based on the scale factor
            slider_min_int = int(min_float * scale)
            slider_max_int = int(max_float * scale)

            label = QLabel(f"{name}:")
            slider = QSlider(Qt.Horizontal)
            # --- MODIFIED: Set slider min/max based on calculated integer ranges ---
            slider.setMinimum(slider_min_int)
            slider.setMaximum(slider_max_int)
            # --- Set initial slider value to corresponding min_val (scaled to int) ---
            slider.setValue(slider_min_int) 
            slider.setTickInterval( (slider_max_int - slider_min_int) // 10 ) # Adjust tick interval for better visual spread
            slider.valueChanged.connect(self.update_slider_values)

            # --- Initialize QLineEdit with the actual float min value ---
            value_display = QLineEdit(f"{min_float:.2f}") 

            value_display.setFixedWidth(60)
            value_display.setReadOnly(True)

            self.slider_labels.append(value_display)
            self.sliders.append(slider)

            grid.addWidget(label, i, 0)
            grid.addWidget(slider, i, 1)
            grid.addWidget(value_display, i, 2)

        slider_group.setLayout(grid)
        layout.addWidget(slider_group)

        # Send button
        send_btn = QPushButton("GASSSS send")
        send_btn.clicked.connect(self.send_pose)
        layout.addWidget(send_btn)

        # Joint angle display
        joint_group = QGroupBox("Live Joint Angles")
        joint_layout = QVBoxLayout()
        for i in range(6):
            joint_label = QLabel(f"Joint {i+1}: --")
            joint_layout.addWidget(joint_label)
            self.joint_labels.append(joint_label)

        joint_group.setLayout(joint_layout)
        layout.addWidget(joint_group)

        self.setLayout(layout)
        self.show()

    def update_slider_values(self):
        for i, slider in enumerate(self.sliders):
            scale = self.coord_configs[i]['scale_factor']
            val = slider.value() / scale
            self.slider_labels[i].setText(f"{val:.2f}")
            self.slider_values[i] = val
            
    def send_pose(self):
        msg = MycobotCoords()
        msg.x, msg.y, msg.z, msg.rx, msg.ry, msg.rz = self.slider_values
        self.pose_pub.publish(msg)
        self.get_logger().info(f"Sent pose: {self.slider_values}")

    def joint_callback(self, msg):
        # Assumes 6 DOF
        for i in range(min(6, len(msg.position))):
            deg = round(msg.position[i] * 180.0 / 3.14159, 1)
            self.joint_labels[i].setText(f"Joint {i+1}: {deg}°")


def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    gui = MyCobotGUI()

    # Run both PyQt5 and rclpy
    timer = gui.create_timer(0.1, lambda: None)
    sys.exit(app.exec_())
    gui.destroy_node()
    rclpy.shutdown()

