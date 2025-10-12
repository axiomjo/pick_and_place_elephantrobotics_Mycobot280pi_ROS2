"""
signal_connector_gui.py - Centralizes all PyQt signal-slot connections.

This module is responsible for wiring up the entire application. It connects:
- ROS facade signals to the appropriate Controller slots.
- User interactions from Views to Controller slots.
- Model signals to View slots for UI updates.
- Controller signals to View slots for status messages.
- Signals between different UI components to keep them synchronized.
"""

class SignalConnector:
    """A dedicated class to handle all signal and slot connections."""
    def __init__(self, orchestrator):
        # (orchestrator: AppOrchestrator) -> None
        self.orchestrator = orchestrator

    def connect_all(self):
        """Wires up all signals and slots for the application."""
        
        # --- Create aliases for readability ---
        # Models
        app_state_model = self.orchestrator.app_state_model
        # Controllers
        ws_ctrl = self.orchestrator.workspace_controller
        simple_cmd_hdlr = self.orchestrator.simple_cmd_handler
        complex_cmd_hdlr = self.orchestrator.complex_cmd_handler
        # Views
        main_win = self.orchestrator.main_window
        action_panel = main_win.action_panel
        cmd_panel = main_win.command_panel
        ws_panel = main_win.workspace_panel
        monitor_panel = main_win.monitor_panel
        # ROS Facade
        ros_comm = self.orchestrator.ros_comm
        
        # ------------------------------------------------------------------
        # 1. ROS Facade (Data In) -> Controllers (Logic)
        # ------------------------------------------------------------------
        ros_comm.detected_objects_received.connect(ws_ctrl.cache_detected_objects)
        ros_comm.annotated_image_received.connect(ws_ctrl.cache_annotated_image)

        # ------------------------------------------------------------------
        # 2. Views (User Input) -> Controllers (Logic)
        # ------------------------------------------------------------------
        # Workspace management buttons
        action_panel.reset_btn.clicked.connect(ws_ctrl.reset_plane)
        action_panel.add_object_btn.clicked.connect(ws_ctrl.add_new_objects_from_cutouts)
        ws_panel.selection_changed.connect(
            lambda items: ws_ctrl.delete_selected(items) if action_panel.delete_btn.isDown() else None
        )

        # Simple command buttons
        cmd_panel.send_rgb_command.connect(simple_cmd_hdlr.handle_rgb_command)
        cmd_panel.send_vacuum_command.connect(simple_cmd_hdlr.handle_vacuum_command)
        cmd_panel.send_coords_command.connect(simple_cmd_hdlr.handle_coords_command)
        cmd_panel.send_home_command.connect(simple_cmd_hdlr.handle_home_command)
        
        # Complex command buttons
        action_panel.analyze_btn.clicked.connect(complex_cmd_hdlr.start_action)
        action_panel.emergency_btn.clicked.connect(complex_cmd_hdlr.cancel_action)

        # ------------------------------------------------------------------
        # 3. Models (Data Changed) -> Views (UI Update)
        # ------------------------------------------------------------------
        # When the app state changes, the action panel updates its button states.
        app_state_model.state_changed.connect(action_panel.update_button_states)
        
        # When the list of workspace items changes, the workspace panel redraws itself.
        # This is already connected inside the WorkspacePanelGUI's constructor.

        # ------------------------------------------------------------------
        # 4. Controllers (Logic Events) -> Views (UI Update)
        # ------------------------------------------------------------------
        # Connect all status message signals to the main window's status bar
        ws_ctrl.status_message_changed.connect(main_win.statusBar().showMessage)
        simple_cmd_hdlr.status_message_changed.connect(main_win.statusBar().showMessage)
        complex_cmd_hdlr.status_message_changed.connect(main_win.statusBar().showMessage)
        
        # Connect the action completion signal to a popup dialog
        complex_cmd_hdlr.action_completed.connect(
            lambda success, msg: QMessageBox.information(main_win, "Action Success", msg) if success else QMessageBox.warning(main_win, "Action Failed", msg)
        )

        # ------------------------------------------------------------------
        # 5. Peer UI Component Connections
        # ------------------------------------------------------------------
        # When an item is selected in the workspace, the command panel's sliders update
        ws_panel.selection_changed.connect(cmd_panel.update_target_sliders_from_selection)
        
        # When new ROS data arrives, the command panel updates its object count display
        ros_comm.detected_objects_received.connect(cmd_panel.update_object_count)

        # ------------------------------------------------------------------
        # 6. ROS Facade (Data In) -> Views (Direct Display) & Views -> ROS Facade (Data Out)
        # ------------------------------------------------------------------
        # Connect ROS image topics directly to the monitor widgets that display them
        ros_comm.undistorted_image_received.connect(monitor_panel.perspective_editor.update_frame)
        ros_comm.annotated_image_received.connect(monitor_panel.annotated_camera.update_camera_view)
        ros_comm.joint_angles_received.connect(monitor_panel.joint_monitor.update_joint_display)

        # Connect the perspective editor's output signal directly to the ROS facade
        monitor_panel.perspective_editor.perspective_points_changed.connect(ros_comm.publish_four_points)

        ros_comm.get_logger().info("All application signals have been connected.")
