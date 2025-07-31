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

import math

class MyCobotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyCobot GUI Controller 31jul")
        
        # --- Initialize rclpy once for the *main thread* (for the publisher) ---
        # It's crucial to initialize rclpy in the thread that will *create* the node.
        # Since self.pose_pub is created directly in this class's __init__ (main thread),
        # rclpy.init() must be called here.
        if not rclpy.ok():
            rclpy.init(args=None)

        # ROS Publisher
        self.minimal_pub_node_name = rclpy.node.Node('mycobot_gui_publisher_node_di_lappy')
        self.pose_pub = self.minimal_pub_node_name.create_publisher(MycobotCoords, 'mycobot_280pi_29jul/pose_goal', 10)
        self.minimal_pub_node_name.get_logger().info("GUI Publisher Node created. udh bisa yapping coords")

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
        self.start_ros_subscriber_thread() 

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
            slider.setMinimum(slider_min_int)
            slider.setMaximum(slider_max_int)
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
        self.minimal_pub_node_name.get_logger().info(f"Sent pose: {self.slider_values}")

    @pyqtSlot(list) # Mark this method as a slot that receives a list
    def update_joint_positions_gui(self, positions):
        """
        This slot is called when the joint_state_received signal is emitted
        from the ROS worker thread. It safely updates the GUI.
        """
        for i in range(min(6, len(positions))):
            rad = positions[i]
            deg = round(rad * 180.0 / math.pi, 1) # Assuming PI is 3.14159 or math.pi
            self.joint_labels[i].setText(f"Joint {i+1}: {deg}°")
        self.minimal_pub_node_name.get_logger().info(f"GUI updated with positions: {positions}") 



    def start_ros_subscriber_thread(self):
        """
        Sets up and starts the QThread for the ROS 2 subscriber node.
        """
        self.ros_signal_emitter = JointStateSignalEmitter()
        # Connect the signal from the ROS subscriber to the GUI's update slot
        self.ros_signal_emitter.joint_state_received.connect(self.update_joint_positions_gui)

        self.ros_thread = QThread()
        # The 'worker' here is actually a simple wrapper that calls the
        # run_ros_node_in_thread function.
        class WorkerWrapper(QObject):
            def __init__(self, signal_emitter):
                super().__init__()
                self.signal_emitter = signal_emitter
            @pyqtSlot()
            def run(self):
                run_ros_node_in_thread(self.signal_emitter)
        
        self.ros_worker = WorkerWrapper(self.ros_signal_emitter)
        self.ros_worker.moveToThread(self.ros_thread)

        # Start the ROS thread when the QThread starts
        self.ros_thread.started.connect(self.ros_worker.run)
        
        # Clean up when the thread finishes
        self.ros_thread.finished.connect(self.ros_thread.deleteLater)
        self.ros_thread.finished.connect(self.ros_worker.deleteLater)

        self.ros_thread.start()
        self.minimal_pub_node_name.get_logger().info("ROS 2 subscriber thread started.")

    def closeEvent(self, event):
        """
        Handles graceful shutdown of the ROS 2 thread when the GUI is closed.
        """
        self.minimal_pub_node_name.get_logger().info("GUI closing: Stopping ROS 2 subscriber thread...")
        self.ros_thread.quit() # Request the thread to exit its event loop
        self.ros_thread.wait() # Wait for the thread to finish execution
        self.minimal_pub_node_name.get_logger().info("ROS 2 subscriber thread stopped.")
        
        # Destroy the publisher node
        if self.minimal_pub_node_name:
            self.minimal_pub_node_name.destroy_node()
            self.minimal_pub_node_name = None # Clear reference

        # Global rclpy shutdown
        if rclpy.ok(): # Check if it's still running before trying to shut down
            rclpy.shutdown()
            
        super().closeEvent(event)

def main(args=None):
    app = QApplication(sys.argv)
    gui = MyCobotGUI()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


