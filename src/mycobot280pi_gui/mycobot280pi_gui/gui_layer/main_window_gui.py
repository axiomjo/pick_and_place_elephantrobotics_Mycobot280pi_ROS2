"""
main_window_gui.py - Defines the MainWindowGUI.

This class is the main window shell for the application. It is a pure View
whose only responsibility is to create and arrange the various panel widgets
that make up the user interface.
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal

# Import the panel Views that this window will contain
from .widgets_gui.monitor_panel_gui import MonitorPanelGUI
from .widgets_gui.workspace_panel_gui import WorkspacePanelGUI
from .widgets_gui.action_panel_gui import ActionPanelGUI
from .widgets_gui.command_panel_gui import CommandPanelGUI

class MainWindowGUI(QMainWindow):
    """The main application window, orchestrating all UI components."""

    # Signal to notify the orchestrator that the window is closing.
    window_closed = pyqtSignal()

    def __init__(self, workspace_model, parent=None):
        # (workspace_model: WorkspaceModel, parent: QWidget) -> None
        """Initializes the main window and sets up the UI."""
        super().__init__(parent)

        self.setWindowTitle("MyCobot 280 Pi GUI (Refactored)")
        self.resize(1400, 900)

        # --- Build UI ---
        # Note that we pass the model to the workspace panel, as it's the one
        # view that needs a direct reference to a model to draw its contents.
        self._setup_ui(workspace_model)

    def _setup_ui(self, workspace_model):
        # (workspace_model: WorkspaceModel) -> None
        """Instantiates all panel widgets and assembles the layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # --- Create child panel widgets ---
        # We pass the model to the WorkspacePanelGUI upon creation.
        self.monitor_panel = MonitorPanelGUI()
        self.workspace_panel = WorkspacePanelGUI(workspace_model)
        self.action_panel = ActionPanelGUI()
        self.command_panel = CommandPanelGUI()

        # --- Assemble Layout ---
        # This layout logic is identical to the old project.
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.workspace_panel)
        right_layout.addWidget(self.action_panel)

        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(self.monitor_panel)
        main_layout.addLayout(right_layout)

        # --- Create Dock Widget ---
        self.dock_widget = QDockWidget("Controls & Cutouts", self)
        self.dock_widget.setWidget(self.command_panel)
        self.dock_widget.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    def closeEvent(self, event):
        # (event: QCloseEvent) -> None
        """
        Overrides the default close event to emit a signal.
        This allows the AppOrchestrator to handle the clean shutdown of ROS.
        """
        self.window_closed.emit()
        event.accept()
