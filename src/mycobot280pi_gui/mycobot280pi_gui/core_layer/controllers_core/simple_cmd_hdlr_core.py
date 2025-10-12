"""
simple_cmd_hdlr_core.py - Defines the SimpleCommandHandler.

This controller handles all simple, direct, "fire-and-forget" style commands
sent to the robot, such as setting LED colors, moving to specific coordinates,
or controlling the vacuum pump. It is triggered by signals from the CommandPanelGUI.
"""

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

# Import type hints for dependencies
from ...ros_layer.ros_facade_bridge import ROS_Facade_Bridge

class SimpleCommandHandler(QObject):
    """Manages the business logic for sending simple service commands."""

    # Signal to send status updates back to the main window's status bar
    status_message_changed = pyqtSignal(str)

    def __init__(self, ros_comm, parent=None):
        # (ros_comm: ROS_Facade_Bridge, parent: QObject)
        super().__init__(parent)
        
        # --- Dependency (Injected) ---
        self.ros_comm = ros_comm
        self.logger = self.ros_comm.get_logger()

        # --- Signal Connections ---
        # Listen for the response from the facade after a command is sent
        self.ros_comm.simple_command_response_received.connect(self._on_command_response)

    # --- Public Slots (for CommandPanelGUI signals) ---

    @pyqtSlot(int, int, int)
    def handle_rgb_command(self, r, g, b):
        """Handles the request to set the robot's LED color."""
        msg = " Sending SET_RGB command | (R={}, G={}, B={})".format(r, g, b)
        self.status_message_changed.emit(msg)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type="set_rgb",
            r=r, g=g, b=b
        )

    @pyqtSlot(str, int, int)
    def handle_vacuum_command(self, cmd_type, pin1, pin2):
        """Handles the request to control the vacuum pump."""
        msg = " Sending VACUUM command | type={}, pin1={}, pin2={}".format(cmd_type, pin1, pin2)
        self.status_message_changed.emit(msg)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type=cmd_type,
            vacuum_pin1_level=pin1,
            vacuum_pin2_level=pin2
        )

    @pyqtSlot(float, float, float, float, float, float, int)
    def handle_coords_command(self, x, y, z, rx, ry, rz, speed):
        """Handles the request to move the robot to a specific 6D pose."""
        full_coords = [x, y, z, rx, ry, rz]
        msg = " Sending MOVE command | coords={}, speed={}".format(full_coords, speed)
        self.status_message_changed.emit(msg)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type="move",
            coords=full_coords,
            speed=speed
        )

    @pyqtSlot()
    def handle_home_command(self):
        """Handles the request to send the robot to its home position."""
        FIXED_HOME_ANGLES = [0, 0, 0, 0, 0, 0]
        MAX_SPEED = 100
        msg = " Sending GO_HOME command | angles={}, speed={}".format(FIXED_HOME_ANGLES, MAX_SPEED)
        self.status_message_changed.emit(msg)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type="move_joints",
            joint_angles=FIXED_HOME_ANGLES,
            speed=MAX_SPEED
        )

    # --- Private Slot (for ROS Facade signals) ---

    @pyqtSlot(bool, str)
    def _on_command_response(self, success, message):
        """Handles the response from the ROS service and formats a status message."""
        if success:
            status = " Command SUCCESS | {}".format(message)
        else:
            status = " Command FAILED | {}".format(message)

        self.status_message_changed.emit(status)
        self.logger.info(status)
