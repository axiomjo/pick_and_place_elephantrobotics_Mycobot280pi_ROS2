#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionServer, GoalResponse, CancelResponse

import math
import time

# -------------------------------
# Imports for msgs & srv
# -------------------------------
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
from mycobot280pi_interfaces.msg import JointAnglesArray
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure
from mycobot280pi_interfaces.action import SimpleCommandsAction


# ============================================================
# ================ 1. DUMMY HARDWARE WRAPPER ==================
# ============================================================
class MycobotHardwareWrapper:
    """
    Dummy hardware wrapper.
    Accepts commands but does nothing.
    """
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("[DUMMY] Hardware wrapper loaded.")
        self._joint_angles = [0, 0, 0, 0, 0, 0]

    def execute_command(self, command_type, coords=None, joint_angles=None,
                        speed=50, r=0, g=0, b=0):

        self.logger.info(f"[DUMMY EXECUTOR] Command = {command_type}")

        if command_type == "move":
            time.sleep(0.05)

        elif command_type == "move_joints":
            if joint_angles and len(joint_angles) == 6:
                self._joint_angles = list(joint_angles)
            time.sleep(0.05)

        elif command_type in ["vacuum_strong", "vacuum_weak", "vacuum_off"]:
            time.sleep(0.02)

        elif command_type == "set_rgb":
            time.sleep(0.02)

        else:
            return False, f"[DUMMY] Unknown command {command_type}"

        return True, f"[DUMMY] Command '{command_type}' done."

    def get_joint_angles(self):
        return list(self._joint_angles)

    def cleanup_hardware(self):
        self.logger.info("[DUMMY] cleanup called.")


# ============================================================
# ============ 2. JOINT STATE + GUI PUBLISHER ================
# ============================================================
class StateAnglesPublisher:
    def __init__(self, node: Node, get_angles_callback):
        self.node = node
        self.get_angles_callback = get_angles_callback

        self.joint_pub = self.node.create_publisher(JointState, "joint_states", 10)
        self.gui_pub = self.node.create_publisher(JointAnglesArray, "/robot/msg_joint_angles", 10)

        self.joint_names = [
            "joint2_to_joint1", "joint3_to_joint2", "joint4_to_joint3",
            "joint5_to_joint4", "joint6_to_joint5", "joint6output_to_joint6"
        ]

        self.timer = self.node.create_timer(1.0/30.0, self.timer_cb)
        self.node.get_logger().info("Publisher ready.")

    def timer_cb(self):
        angles = self.get_angles_callback()
        if not angles or len(angles) != 6:
            return

        # publish joint_states
        rad = [math.radians(x) for x in angles]
        msg = JointState(
            header=Header(stamp=self.node.get_clock().now().to_msg()),
            name=self.joint_names,
            position=rad,
            velocity=[],
            effort=[]
        )
        self.joint_pub.publish(msg)

        # publish GUI message
        gui_msg = JointAnglesArray(joint_angles=list(angles))
        self.gui_pub.publish(gui_msg)

    def destroy(self):
        self.timer.destroy()


# ============================================================
# ============== 3. SIMPLE SERVICE INTERFACE =================
# ============================================================
class SimpleCommandServiceServer:
    def __init__(self, node: Node, execute_callback):
        self.node = node
        self.execute_callback = execute_callback

        self.group = ReentrantCallbackGroup()

        self.srv = self.node.create_service(
            Mycobot280PiSimpleCommandsMadeSure,
            '/gui/srv_simple_command',
            self.cb,
            callback_group=self.group
        )
        self.node.get_logger().info("Service server ready.")

    def cb(self, request, response):
        success, msg = self.execute_callback(
            command_type=request.command_type,
            coords=request.coords,
            joint_angles=request.joint_angles,
            speed=request.speed,
            r=request.r, g=request.g, b=request.b
        )
        response.success = success
        response.message = msg
        return response


# ============================================================
# ================ 4. ACTION SERVER (PLANNER) ================
# ============================================================
class PrimitivesActionServer:
    def __init__(self, node: Node, execute_callback):
        self.node = node
        self.execute_callback = execute_callback
        self.group = ReentrantCallbackGroup()

        self.act = ActionServer(
            node=self.node,
            action_type=SimpleCommandsAction,
            action_name="/planner/act_command_primitives",
            execute_callback=self.exec_cb,
            goal_callback=self.goal_cb,
            cancel_callback=self.cancel_cb,
            callback_group=self.group
        )
        self.node.get_logger().info("Action server ready.")

    def goal_cb(self, goal_request):
        self.node.get_logger().info(f"Goal received: {goal_request.command_type}")
        return GoalResponse.ACCEPT

    def cancel_cb(self, goal_handle):
        self.node.get_logger().info("Cancel request accepted.")
        return CancelResponse.ACCEPT

    def exec_cb(self, goal_handle):
        req = goal_handle.request

        if goal_handle.is_cancel_requested:
            goal_handle.canceled()
            result = SimpleCommandsAction.Result()
            result.success = False
            result.message = "Cancelled."
            return result

        success, msg = self.execute_callback(
            command_type=req.command_type,
            coords=req.coords,
            joint_angles=req.joint_angles,
            speed=req.speed,
            r=req.r, g=req.g, b=req.b
        )

        result = SimpleCommandsAction.Result()
        result.success = success
        result.message = msg

        if success:
            goal_handle.succeed()
        else:
            goal_handle.abort()

        return result


# ============================================================
# ================= 5. MAIN ORCHESTRATOR NODE ================
# ============================================================
class RobotExecutorNode(Node):
    def __init__(self):
        super().__init__('robot_executor_node')

        self.hardware = MycobotHardwareWrapper(self.get_logger())
        self.publisher = StateAnglesPublisher(self, self.hardware.get_joint_angles)
        self.service = SimpleCommandServiceServer(self, self.hardware.execute_command)
        self.action = PrimitivesActionServer(self, self.hardware.execute_command)

        self.get_logger().info("Dummy robot node ready.")

    def cleanup(self):
        self.publisher.destroy()
        self.hardware.cleanup_hardware()


# ============================================================
# ====================== 6. ENTRY POINT =======================
# ============================================================
def main(args=None):
    rclpy.init(args=args)

    node = RobotExecutorNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down.")
    finally:
        executor.shutdown()
        node.cleanup()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

