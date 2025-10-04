"""
grcn_main_window.py - Main application window for the MyCobot 280 Pi GUI.

Acts as the central director:
- Builds and assembles UI components.
- Instantiates managers (state, plane, action, service, selection).
- Connects signals via grcn_signal_connector.
- Maintains cached ROS messages/images.
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget, QMessageBox
from PyQt5.QtCore import Qt

# --- Local imports ---
from ..roscomm.grcn_ros_facade import ROSCommunication

from .widgets.grcn_monitor_panel import MonitorPanel
from .widgets.grcn_workspace_panel import WorkspacePlane
from .widgets.grcn_action_panel import ActionPanel
from .widgets.grcn_command_panel import CommandPanel

# Managers
from .grcn_app_state import AppState, AppStateManager
from .grcn_signal_connector import connect_signals
from .grcn_plane_manager import PlaneManager
from .grcn_selection_manager import SelectionManager
from .grcn_action_manager import ActionManager
from .grcn_commands_manager import ServiceManager


class MainWindow(QMainWindow):
    """The main application window, orchestrating all UI components and ROS communication."""

    def __init__(self):
        super().__init__()

        # 1. Initialize ROS backend
        self.ros_comm = ROSCommunication()
        self.logger = self.ros_comm.get_logger()

        self.setWindowTitle("MyCobot 280 Pi GUI")
        self.resize(1400, 900)

        # --- Cached data from ROS ---
        self.latest_objects_msg = None
        self.latest_annotated_image = None

        # --- Build UI ---
        self.setup_ui()

        # --- Instantiate managers ---
        self.app_state_mgr = AppStateManager(self)
        self.plane_mgr = PlaneManager(self)
        self.selection_mgr = SelectionManager(self)
        self.action_mgr = ActionManager(self, self.ros_comm)
        self.service_mgr = ServiceManager(self, self.ros_comm)

        # --- Wire signals ---
        connect_signals(self)

        # --- Initialize application state ---
        self.app_state_mgr.set_state(AppState.IDLE)
        self.statusBar().showMessage("GUI is Ready.")

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------

    def setup_ui(self):
        """Instantiates all panel widgets and assembles the layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create widgets
        self.monitor_panel = MonitorPanel()
        self.working_plane = WorkspacePlane()
        self.control_panel = ActionPanel()
        self.dock_panel = CommandPanel()

        

        # Layout (camera left, working plane + controls right)
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.working_plane)
        right_layout.addWidget(self.control_panel)

        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(self.monitor_panel)
        main_layout.addLayout(right_layout)

        # Dock widget
        self.dock_widget = QDockWidget("Controls & Cutouts", self)
        self.dock_widget.setWidget(self.dock_panel)
        
        self.dock_widget.setFeatures(
            QDockWidget.DockWidgetFeatures(
                QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable 
            )
        )
        
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    # -------------------------------------------------------------------------
    # Cached ROS Data
    # -------------------------------------------------------------------------

    def cache_detected_objects(self, objects_msg):
        """Caches the latest detected objects message."""
        self.latest_objects_msg = objects_msg
        if self.dock_panel and self.latest_annotated_image is not None:
            self.dock_panel.update_object_count(objects_msg)

    def cache_annotated_image(self, cv_image):
        """Caches the latest annotated image."""
        self.latest_annotated_image = cv_image
        # GUI updates happen via direct signal connections

    # -------------------------------------------------------------------------
    # Shutdown
    # -------------------------------------------------------------------------

    def closeEvent(self, event):
        """Ensures clean shutdown of ROS node when the window is closed."""
        self.logger.info("Shutdown signal received, closing ROS components...")
        self.ros_comm.shutdown()
        event.accept()

