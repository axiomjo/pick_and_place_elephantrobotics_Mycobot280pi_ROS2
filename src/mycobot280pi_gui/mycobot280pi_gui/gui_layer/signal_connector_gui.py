"""
signal_connector_gui.py - Centralizes all PyQt signal-slot connections.
... (docstring) ...
"""
from PyQt5.QtWidgets import QMessageBox

class SignalConnector:
    """A dedicated class to handle all signal and slot connections."""
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def connect_all(self):
        """Wires up all signals and slots for the application."""
        # --- Aliases ---
        app_state_model = self.orchestrator.app_state_model
        ws_ctrl = self.orchestrator.workspace_controller
        simple_cmd_hdlr = self.orchestrator.simple_cmd_handler
        complex_cmd_hdlr = self.orchestrator.complex_cmd_handler
        main_win = self.orchestrator.main_window
        action_panel = main_win.action_panel
        cmd_panel = main_win.command_panel
        ws_panel = main_win.workspace_panel
        monitor_panel = main_win.monitor_panel
        ros_comm = self.orchestrator.ros_comm
        
        # --- 1. ROS Facade -> Controllers ---
        # The ROS message now ONLY caches the data. It does not trigger any action.
        ros_comm.detected_objects_received.connect(ws_ctrl.cache_detected_objects)
        ros_comm.annotated_image_received.connect(ws_ctrl.cache_annotated_image)

        # --- 2. Views -> Controllers ---
        action_panel.reset_btn.clicked.connect(ws_ctrl.reset_plane)
        action_panel.add_object_btn.clicked.connect(ws_ctrl.add_new_objects_from_cutouts)
        action_panel.delete_btn.clicked.connect(ws_ctrl.delete_selected)
        action_panel.add_memory_btn.clicked.connect(ws_ctrl.add_memory_circle)
        
        cmd_panel.send_rgb_command.connect(simple_cmd_hdlr.handle_rgb_command)
        cmd_panel.send_vacuum_command.connect(simple_cmd_hdlr.handle_vacuum_command)
        cmd_panel.send_coords_command.connect(simple_cmd_hdlr.handle_coords_command)
        cmd_panel.send_home_command.connect(simple_cmd_hdlr.handle_home_command)
        
        action_panel.analyze_btn.clicked.connect(complex_cmd_hdlr.start_action)
        action_panel.emergency_btn.clicked.connect(complex_cmd_hdlr.cancel_action)
        # --- 3. Models -> Views ---
        app_state_model.state_changed.connect(action_panel.update_button_states)
        
        # --- 4. Controllers -> Views ---
        ws_ctrl.status_message_changed.connect(main_win.statusBar().showMessage)
        simple_cmd_hdlr.status_message_changed.connect(main_win.statusBar().showMessage)
        complex_cmd_hdlr.status_message_changed.connect(main_win.statusBar().showMessage)
        complex_cmd_hdlr.action_completed.connect(
            lambda success, msg: QMessageBox.information(main_win, "Action Success", msg) if success else QMessageBox.warning(main_win, "Action Failed", msg)
        )

        # --- 5. Peer UI Component Connections ---
        ws_panel.selection_changed.connect(ws_ctrl.cache_current_selection)
        ws_panel.selection_changed.connect(cmd_panel.update_target_sliders_from_selection)
        ros_comm.detected_objects_received.connect(cmd_panel.update_object_count)

        action_panel.rotate_clockwise_btn.clicked.connect(ws_panel.rotate_selected_clockwise)
        action_panel.rotate_counter_clockwise_btn.clicked.connect(ws_panel.rotate_selected_counter_clockwise)
        
        # --- 6. ROS <-> UI Direct Connections ---
        ros_comm.undistorted_image_received.connect(monitor_panel.perspective_editor.update_frame)
        ros_comm.annotated_image_received.connect(monitor_panel.annotated_camera.update_camera_view)
        ros_comm.annotated_image_received.connect(ws_ctrl.cache_annotated_image)
        ros_comm.joint_angles_received.connect(monitor_panel.joint_monitor.update_joint_display)
        monitor_panel.perspective_editor.perspective_points_changed.connect(ros_comm.publish_four_points)

        ros_comm.get_logger().info("All application signals have been connected.")
