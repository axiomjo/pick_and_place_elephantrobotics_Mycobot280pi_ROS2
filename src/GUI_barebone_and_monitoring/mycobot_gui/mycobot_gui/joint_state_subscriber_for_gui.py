# This module contains the ROS 2 subscriber node that runs in a separate thread
# and communicates received data to the GUI via PyQt signals.

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor # Explicitly import MultiThreadedExecutor
from sensor_msgs.msg import JointState # Import the message type for JointState

# Import PyQt mechanisms for inter-thread communication
from PyQt5.QtCore import QObject, pyqtSignal # For PyQt5. Use PySide2.QtCore for PySide2

class JointStateSignalEmitter(QObject):
    """
    A QObject to emit signals from the ROS worker thread to the GUI thread.
    This acts as the 'message board' for the ROS worker to update the GUI.
    """
    # Define a signal that will carry the joint positions (list of floats)
    # The GUI's slot will connect to this signal.
    joint_state_received = pyqtSignal(list) 

class ROS2SubscriberNode(Node):
    """
    Dedicated ROS 2 node for subscribing to joint states.
    This node runs in a separate thread and emits PyQt signals
    to update the GUI. It acts as the "joint_state_subscriber_for_gui".
    """
    def __init__(self, signal_emitter_obj):
        # Initialize the ROS 2 node with a unique name
        super().__init__("joint_state_subscriber_for_gui_node")
        self.get_logger().info("ROS2SubscriberNode: Initializing as background listener...")

        # Store the signal emitter object provided by the GUI
        self.signal_emitter = signal_emitter_obj

        # Create a subscription to the 'joint_states' topic
        # The 'joint_callback' method will be called every time a message is received.
        self.subscription = self.create_subscription(
            msg_type=JointState,
            topic="joint_states",
            callback=self.joint_callback,
            qos_profile=10 # Quality of Service profile (standard for real-time data)
        )
        self.get_logger().info("ROS2SubscriberNode: Subscribing to topic: /joint_states")

    def joint_callback(self, msg: JointState):
        """
        Callback function for the JointState subscriber.
        This function is executed every time a JointState message is received.
        It then emits a PyQt signal to update the GUI.
        """
        # Ensure we have at least 6 positions (standard for MyCobot 280/280Pi)
        if len(msg.position) >= 6:
            # Emit the signal with the joint positions (ensure it's a list)
            # The GUI's connected slot will receive this data in its main thread.
            self.signal_emitter.joint_state_received.emit(list(msg.position[:6]))
            # self.get_logger().info(f"ROS2SubscriberNode: Emitted joint states to GUI.") # Uncomment for verbose logging
        else:
            self.get_logger().warn(f"ROS2SubscriberNode: Received JointState with {len(msg.position)} joints, expected 6. Skipping update.")

# --- This function is the entry point for the QThread ---
def run_ros_node_in_thread(signal_emitter_obj):
    """
    This function initializes rclpy (if not already initialized in this thread),
    creates and adds the ROS2SubscriberNode to a MultiThreadedExecutor,
    and then spins the executor.
    This is designed to be called from the 'run' method of a QThread.
    """
    # Initialize rclpy if it hasn't been initialized in this specific thread/context.
    # rclpy.init() ensures the ROS client library is ready to use.
    if not rclpy.ok():
        rclpy.init(args=None)

    # Create an instance of our ROS 2 subscriber node, passing it the signal emitter
    # so it can communicate with the GUI.
    node = ROS2SubscriberNode(signal_emitter_obj)
    
    # Create a MultiThreadedExecutor. This manager can handle tasks concurrently,
    # making the node more responsive if it has multiple subscriptions/timers.
    executor = MultiThreadedExecutor()
    
    # Add our subscriber node to this executor. The executor will now manage its callbacks.
    executor.add_node(node)

    try:
        node.get_logger().info("ROS2SubscriberNode: Executor spinning...")
        # Start the executor. This is a blocking call that keeps the node alive
        # and processing callbacks until the executor is shut down.
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info("ROS2SubscriberNode: KeyboardInterrupt caught, shutting down executor.")
    finally:
        # Clean up resources when the executor stops or an error occurs.
        executor.shutdown() # Shuts down the executor and stops managing nodes
        node.destroy_node() # Destroys the ROS 2 node, releasing its resources
        # rclpy.shutdown() # Generally called once by the main process (GUI's closeEvent)
