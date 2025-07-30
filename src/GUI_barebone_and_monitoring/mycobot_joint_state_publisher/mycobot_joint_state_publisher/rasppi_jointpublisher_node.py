import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

from std_msgs.msg import Header

import pymycobot
from pymycobot.mycobot import MyCobot, PI_PORT, PI_BAUD

class MyCobotRealJointPublisher(Node):
    def __init__(self):
        super().__init__("mycobot_joint_publisher_node_di_rasppi") 

        self.get_logger().info(f"Connecting to MyCobot on port:{PI_PORT}, baud:{PI_BAUD}")
        self.mc = MyCobot(PI_PORT, PI_BAUD)

        self.get_logger().info("MyCobot Joint Publisher Node is ready. udh bisa yapping kondisi tiap joint robotnya :D")
        self.start_publishing() # Call a method to encapsulate publishing logic

    def start_publishing(self):
        pub = self.create_publisher(
            msg_type=JointState,
            topic="joint_states", # Standard topic for joint states
            qos_profile=10
        )
        rate = self.create_rate(30)  # 30hz

        # pub joint state
        joint_state_send = JointState()
        joint_state_send.header = Header()

        # You might want to align these names with your URDF if you have one
        # These names should match your robot's joint names in its URDF description
        joint_state_send.name = [
            "joint2_to_joint1",
            "joint3_to_joint2",
            "joint4_to_joint3",
            "joint5_to_joint4",
            "joint6_to_joint5",
            "joint6output_to_joint6",
        ]

        joint_state_send.velocity = [] # Can be left empty if not publishing velocity
        joint_state_send.effort = [] # Can be left empty if not publishing effort

        while rclpy.ok():
            # get real angles from server.
            res = self.mc.get_angles()
            try:
                # Check for valid data (e.g., if all angles are 0.0 it might mean connection issue)
                if not res or len(res) != 6 or all(angle == 0.0 for angle in res):
                    self.get_logger().warn("Received invalid angles, skipping publication. uh.. keknya ada yg broken, s e k i p s e k")
                    rclpy.spin_once(self, timeout_sec=0) # Process callbacks even if skipping
                    rate.sleep()
                    continue

                radians_list = [
                    res[0] * (math.pi / 180),
                    res[1] * (math.pi / 180),
                    res[2] * (math.pi / 180),
                    res[3] * (math.pi / 180),
                    res[4] * (math.pi / 180),
                    res[5] * (math.pi / 180),
                ]
                self.get_logger().info("Publishing angles: {}".format(radians_list)) # Uncomment for verbose logging

                # publish angles.
                joint_state_send.header.stamp = self.get_clock().now().to_msg()
                joint_state_send.position = radians_list
                pub.publish(joint_state_send)
            except Exception as e:
                self.get_logger().error(f"Error getting or publishing angles: {e}")

            rclpy.spin_once(self, timeout_sec=0) # Process any pending callbacks
            rate.sleep()


def main(args=None):
    rclpy.init(args=args)

    mycobot_publisher_node = MyCobotRealJointPublisher()
    # The publishing loop is now inside the start_publishing method, called from __init__
    # rclpy.spin will keep the node alive and process its timers/publishers
    rclpy.spin(mycobot_publisher_node)

    mycobot_publisher_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
