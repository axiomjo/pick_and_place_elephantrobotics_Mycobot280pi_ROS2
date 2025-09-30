"""
grcn_service_manager.py - Handles GUI-side orchestration of ROS 2 services.

This module connects GUI user intents (buttons) with the ROS service client
logic provided by roscomm/handlers/grcn_service_client_handler.py.
"""

from .widgets.grcn_draggable_item import DraggableItem


class ServiceManager:
    """Manages sending service requests and handling responses."""

    def __init__(self, main_window, ros_comm):
        """
        :param main_window: Reference to the QMainWindow (for status bar updates).
        :param ros_comm: Reference to ROSCommunication facade.
        """
        self.main_window = main_window
        self.ros_comm = ros_comm
        self.logger = ros_comm.get_logger()

        # Connect ROS signals to our handlers
        self.ros_comm.simple_command_response.connect(self._on_response)

    # -------------------------------------------------------------------------
    # GUI → ROS (Send Service Request)
    # -------------------------------------------------------------------------

    def send_service_request(self):
        """Sends a simple command service request for the selected DraggableItem."""
        selected_items = self.main_window.working_plane.working_plane_scene.selectedItems()

        if not selected_items or not isinstance(selected_items[0], DraggableItem):
            self.main_window.statusBar().showMessage("No valid item selected for simple command.", 3000)
            return

        item = selected_items[0]
        center_pos = item.mapToScene(item.boundingRect().center())
        rot = item.rotation()

        # Example coordinates (adjust as needed for your robot)
        coords = [center_pos.x(), center_pos.y(), 60.0, 180.0, 0.0, rot]

        self.logger.info(f"Sending service request with coords: {coords}")
        self.ros_comm.call_simple_command(coords=coords, speed=80, is_linear_mode=False)

    # -------------------------------------------------------------------------
    # ROS → GUI (Response Handling)
    # -------------------------------------------------------------------------

    def _on_response(self, success: bool, message: str):
        """Handles the response from the simple command service."""
        self.main_window.statusBar().showMessage(f"Simple Command: {message}", 4000)

