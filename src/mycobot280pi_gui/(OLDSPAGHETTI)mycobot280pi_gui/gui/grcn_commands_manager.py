from .widgets.components.graphics.grcn_draggable_item import DraggableItem

from PyQt5.QtCore import pyqtSlot # Import for signal handling
from mycobot280pi_interfaces.msg import SimpleCommands  

class ServiceManager:
    """Manages sending service requests and handling responses for ALL simple commands."""

    def __init__(self, main_window, ros_comm):
        """
        :param main_window: Reference to the QMainWindow (for status bar updates).
        :param ros_comm: Reference to ROSCommunication facade.
        """
        self.main_window = main_window
        self.ros_comm = ros_comm
        self.logger = ros_comm.get_logger()

        # Connect ROS signals to our handlers
        self.ros_comm.simple_command_response_received.connect(self._on_response)

    # -------------------------------------------------------------------------
    # GUI → ROS (Send Service Request for MOVE/OLD BUTTON)
    # -------------------------------------------------------------------------

    def send_service_request(self):
        """Sends a MOVE command service request for the selected DraggableItem (from Control Panel's old button)."""
        selected_items = self.main_window.working_plane.working_plane_scene.selectedItems()

        if not selected_items or not isinstance(selected_items[0], DraggableItem):
            self.main_window.statusBar().showMessage("⚠️ No valid item selected for MOVE command.", 3000)
            return

        item = selected_items[0]
        center_pos = item.mapToScene(item.boundingRect().center())
        rot = item.rotation()

        coords = [center_pos.x(), center_pos.y(), 60.0, 180.0, 0.0, rot]

        msg = f"➡️ Sending OLD MOVE command | coords={coords}, speed=80"
        self.main_window.statusBar().showMessage(msg, 4000)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type="move",
            coords=coords, 
            speed=80, 
            joint_angles=[], 
        )

    # -------------------------------------------------------------------------
    # GUI → ROS (NEW Dock Panel Command Handlers)
    # -------------------------------------------------------------------------

    def handle_rotation_command(self, rz_angle: float):
        """Handles RZ rotation command from the DockPanel."""
        msg = f"➡️ Sending RZ_ROTATION command | rz_angle={rz_angle}"
        self.main_window.statusBar().showMessage(msg, 4000)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type="set_rz_angle",
            coords=[0.0, 0.0, 0.0, 0.0, 0.0, rz_angle]
        )

    def handle_rgb_command(self, r: int, g: int, b: int):
        """Handles RGB command from the DockPanel."""
        msg = f"➡️ Sending SET_RGB command | (R={r}, G={g}, B={b})"
        self.main_window.statusBar().showMessage(msg, 4000)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type="set_rgb",
            r=r,
            g=g,
            b=b
        )

    def handle_vacuum_command(self, cmd_type: str, pin1: int, pin2: int):
        """Handles Vacuum command from the DockPanel."""
        msg = f"➡️ Sending VACUUM command | type={cmd_type}, pin1={pin1}, pin2={pin2}"
        self.main_window.statusBar().showMessage(msg, 4000)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type=cmd_type,
            vacuum_pin1_level=pin1,
            vacuum_pin2_level=pin2
        )

    def handle_coords_command(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, speed: int):
        """Handles MOVE command from the DockPanel."""
        full_coords = [x, y, z, rx, ry, rz]
        msg = f"➡️ Sending MOVE command | coords={full_coords}, speed={speed}"
        self.main_window.statusBar().showMessage(msg, 4000)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type="move",
            coords=full_coords,
            speed=speed
        )

    def handle_home_command(self):
        """Membuat dan mengirim pesan ROS untuk perintah GO HOME."""
        FIXED_HOME_ANGLES = [0, 0, 0, 0, 0, 0]
        MAX_SPEED = 100
        msg = f"➡️ Sending GO_HOME command | angles={FIXED_HOME_ANGLES}, speed=MAX_SPEED"
        self.main_window.statusBar().showMessage(msg, 4000)
        self.logger.info(msg)

        self.ros_comm.call_simple_command(
            command_type="move_joints",
            joint_angles=FIXED_HOME_ANGLES,
            speed=MAX_SPEED
        )

    # -------------------------------------------------------------------------
    # ROS → GUI (Response Handling)
    # -------------------------------------------------------------------------

    def _on_response(self, success: bool, message: str):
        """Handles the response from the simple command service and updates status."""
        if success:
            status = f"✅ Command SUCCESS | {message}"
        else:
            status = f"❌ Command FAILED | {message}"

        self.main_window.statusBar().showMessage(status, 4000)
        self.logger.info(status)

