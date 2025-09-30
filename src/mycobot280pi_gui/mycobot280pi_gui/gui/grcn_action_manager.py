"""
grcn_action_manager.py - Handles GUI-side orchestration of ROS 2 actions.
"""

from PyQt5.QtWidgets import QMessageBox
from mycobot280pi_interfaces.msg import ManyDetectedObjects, Point2DArray, Point2D

from .widgets.grcn_draggable_item import DraggableItem
from .grcn_app_state import AppState


class ActionManager:
    """Manages starting, canceling, and handling feedback/results of actions."""

    def __init__(self, main_window, ros_comm):
        self.main_window = main_window
        self.ros_comm = ros_comm
        self.logger = ros_comm.get_logger()

        self.ros_comm.action_feedback.connect(self._on_feedback)
        self.ros_comm.action_result.connect(self._on_result)

    def start_action(self):
        """Collects moved items and sends a complex action goal to ROS."""
        moved_items = [
            item for item in self.main_window.working_plane.items_on_plane if item.was_moved
        ]

        if not moved_items:
            QMessageBox.warning(
                self.main_window, "Error", "No items have been moved to a new target position."
            )
            return

        self.main_window.statusBar().showMessage("Preparing action goal for moved items...")

        objects_to_move = ManyDetectedObjects()
        target_positions = Point2DArray()
        target_orientations = []

        for item in moved_items:
            objects_to_move.objects.append(item.detected_object)

            new_pos_scene = item.scenePos()
            target_pt = Point2D()
            target_pt.x = new_pos_scene.x()
            target_pt.y = new_pos_scene.y()
            target_positions.points.append(target_pt)
            target_orientations.append(int(item.rotation()))

        self.ros_comm.send_complex_goal(objects_to_move, target_positions, target_orientations)

        self.main_window.app_state_mgr.set_state(AppState.BUSY)

    def cancel_action(self):
        """Cancels the ongoing complex action via ROS."""
        self.logger.info("Cancel button clicked.")
        self.ros_comm.cancel_complex_goal()

    def _on_feedback(self, current_state: str):
        """Displays live feedback in the GUI status bar."""
        self.main_window.statusBar().showMessage(f"Action Progress: {current_state}")

    def _on_result(self, success: bool, message: str):
        """Handles the final result of the action and updates GUI state."""
        self.main_window.statusBar().showMessage(f"Action Finished: {message}", 5000)
        self.main_window.app_state_mgr.set_state(AppState.FINISHED)

        if success:
            QMessageBox.information(self.main_window, "Action Success", message)
        else:
            QMessageBox.warning(self.main_window, "Action Failed / Cancelled", message)

