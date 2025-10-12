"""
complex_cmd_hdlr_core.py - Defines the ComplexCommandHandler.

This controller manages the logic for the main, multi-step "pick and place"
task. It is triggered by the user, changes the application state, gets data
from the workspace model, and sends the goal to the ROS backend.
"""

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

# Import the models it interacts with
from ..app_state_model_core import AppStateModel
from ..workspace_model_core import WorkspaceModel
from ..state_enum_core import AppState

# Import type hints for dependencies and ROS messages
from ...ros_layer.ros_facade_bridge import ROS_Facade_Bridge
from mycobot280pi_interfaces.msg import ManyDetectedObjects, Point2DArray, Point2D

class ComplexCommandHandler(QObject):
    """Manages the business logic for the complex pick-and-place action."""

    # Signal for general status updates (e.g., for the status bar)
    status_message_changed = pyqtSignal(str)
    
    # A more specific signal to trigger a popup dialog on completion
    action_completed = pyqtSignal(bool, str)

    def __init__(self, app_state_model, workspace_model, ros_comm, parent=None):
        # (app_state_model: AppStateModel, workspace_model: WorkspaceModel, 
        #  ros_comm: ROS_Facade_Bridge, parent: QObject)
        super().__init__(parent)
        
        # --- Dependencies (Injected) ---
        self.app_state_model = app_state_model
        self.workspace_model = workspace_model
        self.ros_comm = ros_comm
        self.logger = self.ros_comm.get_logger()

        # --- Signal Connections ---
        # Listen for feedback and results from the ROS action via the facade
        self.ros_comm.action_feedback.connect(self._on_action_feedback)
        self.ros_comm.action_result.connect(self._on_action_result)

    # --- Public Slots (for ActionPanelGUI signals) ---

    @pyqtSlot()
    def start_action(self):
        """
        Initiates the complex pick-and-place action.
        This is the main logic migrated from the old ActionManager.
        """
        # Safety check: Do not start a new action if one is already running.
        if self.app_state_model.get_state() != AppState.IDLE:
            self.logger.warn("'Start Action' was triggered while not in IDLE state.")
            return

        self.logger.info("Preparing complex action goal...")
        self.status_message_changed.emit("Preparing action goal for moved items...")

        # 1. Immediately set the application state to BUSY.
        self.app_state_model.set_state(AppState.BUSY)
        
        # 2. Get data from the WorkspaceModel.
        all_items = self.workspace_model.get_all_items()
        moved_items = [item for item in all_items if item.was_moved]

        # 3. Handle the case where no items were moved.
        if not moved_items:
            self.status_message_changed.emit("Error: No items have been moved to a new position.")
            self.logger.warn("Action start aborted: No items were moved.")
            # Set state back to IDLE as the action was aborted.
            self.app_state_model.set_state(AppState.IDLE)
            return

        # 4. Prepare the ROS goal message from the model data.
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

        # 5. Send the goal via the ROS Facade.
        self.ros_comm.send_complex_goal(
            objects_to_move, target_positions, target_orientations
        )

    @pyqtSlot()
    def cancel_action(self):
        """Requests cancellation of the ongoing complex action."""
        self.logger.info("Cancel action requested by user.")
        self.ros_comm.cancel_complex_goal()

    # --- Private Slots (for ROS Facade signals) ---

    @pyqtSlot(str)
    def _on_action_feedback(self, feedback_message):
        """Receives live feedback from the action and relays it as a status message."""
        self.status_message_changed.emit("Action Progress: {}".format(feedback_message))

    @pyqtSlot(bool, str)
    def _on_action_result(self, success, result_message):
        """Handles the final result of the action."""
        self.logger.info("Complex action finished. Success: {}, Message: {}".format(success, result_message))
        self.status_message_changed.emit("Action Finished: {}".format(result_message))
        
        # 1. Set the final application state.
        self.app_state_model.set_state(AppState.FINISHED)
        
        # 2. Emit a specific signal to trigger a result popup.
        self.action_completed.emit(success, result_message)
