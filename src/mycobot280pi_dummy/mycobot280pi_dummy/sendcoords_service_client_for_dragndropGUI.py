# sendcoords_service_client_for_dragndropGUI.py

import rclpy
from rclpy.node import Node
from mycobot280pi_interfaces.srv import Mycobot280PiSimpleCommandsMadeSure
from PyQt5.QtCore import QObject, QThread, pyqtSignal


class SendCoordsSignalEmitter(QObject):
    """Qt signals bridged from the ROS2 side back to the GUI."""
    service_ready_signal = pyqtSignal(bool)   # True when /set_coords is available
    response_received_signal = pyqtSignal(object)  # srv response object (or None on error)


class SendCoordsServiceClientNode(QThread):
    """
    QThread that owns the ROS 2 client node and spins it in the background.
    - Creates a Node and a Client for mycobot_interfaces/srv/SetCoords.
    - Waits for /set_coords to appear.
    - Emits Qt signals when the service is (un)available and on response.
    """
    def __init__(self, signal_emitter: SendCoordsSignalEmitter):
        super().__init__()
        self.signal_emitter = signal_emitter
        self.node: Node | None = None
        self.cli = None
        self.future = None
        self._running = True
        self._service_ready = False
        self._rclpy_inited = False

    def run(self):
        # Initialize ROS 2 inside THIS thread
        rclpy.init(args=None)
        self._rclpy_inited = True

        self.node = Node("sendcoords_service_client_node")
        self.cli = self.node.create_client(Mycobot280PiSimpleCommandsMadeSure, "/set_coords")

        self.node.get_logger().info("ROS 2 client node started. Waiting for /set_coords ...")

        # Wait (non-busy) until service appears. Still cancellable via _running.
        while self._running and rclpy.ok():
            if self.cli.wait_for_service(timeout_sec=0.5):
                self._service_ready = True
                self.node.get_logger().info("Service /set_coords is available ✅")
                self.signal_emitter.service_ready_signal.emit(True)
                break
            else:
                self.node.get_logger().warn("Waiting for /set_coords ...")

        # Spin loop: process callbacks & futures
        while self._running and rclpy.ok() and self.node is not None:
            # Deliver callbacks, timers, responses, etc.
            rclpy.spin_once(self.node, timeout_sec=0.1)

            # If you ever want to re-check availability dynamically, you could:
            # ready_now = self.cli.service_is_ready()
            # if ready_now != self._service_ready:
            #     self._service_ready = ready_now
            #     self.signal_emitter.service_ready_signal.emit(ready_now)

            # If a request is in-flight, check for completion
            if self.future is not None and self.future.done():
                try:
                    response = self.future.result()
                    self.signal_emitter.response_received_signal.emit(response)
                    self.node.get_logger().info("Service response received ✅")
                except Exception as e:
                    self.node.get_logger().error(f"Service call failed: {e}")
                    self.signal_emitter.response_received_signal.emit(None)
                finally:
                    self.future = None

        # Cleanup
        if self.node is not None:
            self.node.destroy_node()
            self.node = None
        if self._rclpy_inited:
            rclpy.shutdown()
            self._rclpy_inited = False

    def call_async_service(self, req: Mycobot280PiSimpleCommandsMadeSure.Request):
        if not self._service_ready or self.cli is None:
            if self.node:
                self.node.get_logger().error("Service not ready, cannot send request ❌")
            return
        self.future = self.cli.call_async(req)
        if self.node:
            self.node.get_logger().info("Service request sent ✅")

    def stop(self):
        # Tell the loop to exit and wait for thread to finish
        self._running = False
        self.quit()
        self.wait()

