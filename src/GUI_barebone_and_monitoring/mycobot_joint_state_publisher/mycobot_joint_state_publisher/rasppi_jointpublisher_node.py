import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

from std_msgs.msg import Header

import pymycobot
from pymycobot import MyCobot, PI_PORT, PI_BAUD

class MyCobotRealJointPublisher(Node):
    def __init__(self):
        super().__init__("mycobot_joint_publisher_node_di_rasppi") 

        self.get_logger().info(f"Connecting to MyCobot on port:{PI_PORT}, baud:{PI_BAUD}")
        self.mc = MyCobot(PI_PORT, PI_BAUD)

        self.publisher = self.create_publisher(
            JointState,
            "joint_states",
            qos_profile=10
        )

        self.joint_names = [
            "joint2_to_joint1",
            "joint3_to_joint2",
            "joint4_to_joint3",
            "joint5_to_joint4",
            "joint6_to_joint5",
            "joint6output_to_joint6",
        ]

        timer_period = 1.0 / 30.0  # 30 Hz
        self.timer = self.create_timer(timer_period, self.publish_joint_states)
        self.get_logger().info("MyCobot Joint Publisher Node is ready to Y A P P P.")

    def publish_joint_states(self):
        try:
            res = self.mc.get_angles()
            if not res or len(res) != 6 or all(angle == 0.0 for angle in res):
                self.get_logger().warn("Invalid joint angles received. Skipping.")
                return

            radians_list = [math.radians(angle) for angle in res]

            joint_state_msg = JointState()
            joint_state_msg.header = Header()
            joint_state_msg.header.stamp = self.get_clock().now().to_msg()
            joint_state_msg.name = self.joint_names
            joint_state_msg.position = radians_list
            joint_state_msg.velocity = []
            joint_state_msg.effort = []

            self.publisher.publish(joint_state_msg)
            self.get_logger().debug(f"Published: {radians_list}")

        except Exception as e:
            self.get_logger().error(f"Error while publishing joint states: {e}")

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
