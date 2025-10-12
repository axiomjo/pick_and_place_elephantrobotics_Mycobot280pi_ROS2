"""
app_orchestrator_core.py - Defines the AppOrchestrator.

This is the master class that constructs and owns all major components of the
application (Models, Views, Controllers, and the ROS Facade). It is responsible
for the entire application lifecycle.
"""
from PyQt5.QtCore import QObject, pyqtSlot

# Import all the major components it needs to build
from .ros_layer.ros_facade_bridge import ROS_Facade_Bridge
from .core_layer.workspace_model_core import WorkspaceModel
from .core_layer.app_state_model_core import AppStateModel
from .core_layer.controllers_core.workspace_ctrl_core import WorkspaceController
from .core_layer.controllers_core.simple_cmd_hdlr_core import SimpleCommandHandler
from .core_layer.controllers_core.complex_cmd_hdlr_core import ComplexCommandHandler
from .gui_layer.main_window_gui import MainWindowGUI
from .gui_layer.signal_connector_gui import SignalConnector

class AppOrchestrator(QObject):
    """The central orchestrator that builds and connects the application."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # --- 1. Create Communication Bridge ---
        self.ros_comm = ROS_Facade_Bridge()

        # --- 2. Create Models (The Data) ---
        self.workspace_model = WorkspaceModel()
        self.app_state_model = AppStateModel()

        # --- 3. Create Controllers (The Logic) and inject dependencies ---
        self.workspace_controller = WorkspaceController(
            model=self.workspace_model, 
            ros_comm=self.ros_comm
        )
        self.simple_cmd_handler = SimpleCommandHandler(
            ros_comm=self.ros_comm
        )
        self.complex_cmd_handler = ComplexCommandHandler(
            app_state_model=self.app_state_model, 
            workspace_model=self.workspace_model, 
            ros_comm=self.ros_comm
        )

        # --- 4. Create Views (The UI) and inject dependencies ---
        # The main window needs the workspace model to pass to its child widget
        self.main_window = MainWindowGUI(workspace_model=self.workspace_model)

        # --- 5. Wire everything together ---
        # The connector needs access to all components to connect them
        self.connector = SignalConnector(self)
        self.connector.connect_all()

        # --- 6. Show the UI ---
        self.main_window.show()
        self.main_window.statusBar().showMessage("GUI is Ready.")

        # --- 7. Connect shutdown signal ---
        self.main_window.window_closed.connect(self.shutdown)
        
    @pyqtSlot()
    def shutdown(self):
        """Handles the clean shutdown of the application."""
        self.ros_comm.get_logger().info("Shutdown signal received from main window...")
        self.ros_comm.shutdown()
