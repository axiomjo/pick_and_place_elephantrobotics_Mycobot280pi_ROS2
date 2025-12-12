
import rclpy
from rclpy.node import Node
import math
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
from mycobot280pi_interfaces.msg import JointAnglesArray 

TOPIC_JOINT_ANGLES = '/robot/msg_joint_angles'

class StateAnglesPublisher:
    """
    Manages the status publisher interface, fetching and publishing 
    joint state data periodically.
    """
    def __init__(self, node: Node, get_angles_callback):
        self.node = node
        # The method from the Orchestrator node to fetch current angles
        self.get_angles_callback = get_angles_callback 
        
        self.joint_state_pub = self.node.create_publisher(JointState, "joint_states", 10)
        self.gui_pub = self.node.create_publisher(JointAnglesArray, TOPIC_JOINT_ANGLES, 10)
        
        self.joint_names = [
            "joint2_to_joint1", "joint3_to_joint2", "joint4_to_joint3",
            "joint5_to_joint4", "joint6_to_joint5", "joint6output_to_joint6"
        ]

        # Timer for publishing joint states (30 Hz)
        self.status_timer = self.node.create_timer(1.0 / 30.0, self.publish_joint_states_callback)
        self.node.get_logger().info("Status Publisher running.")

    def publish_joint_states_callback(self):
        """Fetches and publishes joint states for ROS and GUI."""
        angles_degrees = self.get_angles_callback()
        
        if angles_degrees is None or len(angles_degrees) != 6:
            # self.node.get_logger().warn("Could not retrieve 6 joint angles.")
            return

        # Publish to 'joint_states' topic (in radians)
        radians_list = [math.radians(a) for a in angles_degrees]
        joint_state_msg = JointState(
            header=Header(stamp=self.node.get_clock().now().to_msg()),
            name=self.joint_names,
            position=radians_list,
            velocity=[],
            effort=[]
        )
        self.joint_state_pub.publish(joint_state_msg)

        # Publish to GUI topic (in degrees)
        array_msg = JointAnglesArray(joint_angles=[float(a) for a in angles_degrees])
        self.gui_pub.publish(array_msg)

    def destroy(self):
        """Stops the timer for clean shutdown."""
        self.status_timer.destroy()
