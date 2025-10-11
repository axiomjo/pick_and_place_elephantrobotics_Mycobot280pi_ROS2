"""
grcn_signal_connector.py - Centralizes all PyQt signal-slot connections.

This module is responsible for wiring up the entire application. It connects:
- ROS facade signals for data updates to the appropriate GUI widgets.
- User interactions from control panels to the logic in the managers.
- Signals and slots between different UI components to keep them synchronized.

This decoupled approach makes the individual components more modular and easier
to test and maintain.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .grcn_main_window import MainWindow


def connect_signals(main_window: 'MainWindow'):
    """
    Wires up all signals and slots for the application.

    :param main_window: The main QMainWindow instance which holds references
                        to all managers and UI panel widgets.
    """
    # --- Create aliases for managers and panels to improve readability ---
    ros_comm = main_window.ros_comm
    action_mgr = main_window.action_mgr
    service_mgr = main_window.service_mgr
    plane_mgr = main_window.plane_mgr
    selection_mgr = main_window.selection_mgr

    monitor_panel = main_window.monitor_panel
    control_panel = main_window.control_panel
    dock_panel = main_window.dock_panel
    working_plane = main_window.working_plane
    
    annotated_camera = main_window.monitor_panel.annotated_camera
    joint_monitor = main_window.monitor_panel.joint_monitor
    
    # -------------------------------------------------------------------------
    # ROS → GUI (data updates)
    # -------------------------------------------------------------------------
    ros_comm.detected_objects_received.connect(main_window.cache_detected_objects)
    ros_comm.annotated_image_received.connect(main_window.cache_annotated_image)
    ros_comm.undistorted_image_received.connect(monitor_panel.perspective_editor.update_frame)
    ros_comm.annotated_image_received.connect(annotated_camera.update_camera_view)
    ros_comm.joint_angles_received.connect(joint_monitor.update_joint_display)
    

    # -------------------------------------------------------------------------
    # Control Panel → Managers
    # -------------------------------------------------------------------------
    control_panel.analyze_btn.clicked.connect(action_mgr.start_action)
    control_panel.emergency_btn.clicked.connect(action_mgr.cancel_action)
    control_panel.reset_btn.clicked.connect(plane_mgr.reset_plane)
    control_panel.add_object_btn.clicked.connect(plane_mgr.add_new_objects_from_cutouts)
    control_panel.delete_btn.clicked.connect(plane_mgr.delete_selected)

    # -------------------------------------------------------------------------
    # Control Panel (rotation) → Working Plane
    # -------------------------------------------------------------------------
    control_panel.rotate_clockwise_btn.clicked.connect(working_plane.rotate_clockwise)
    control_panel.rotate_counter_clockwise_btn.clicked.connect(working_plane.rotate_counter_clockwise)

    # -------------------------------------------------------------------------
    # Peer UI Component Connections
    # -------------------------------------------------------------------------
    # Working Plane selection changes update the status bar (via selection manager)
    working_plane.working_plane_scene.item_selected.connect(selection_mgr.set_selected_item)
    working_plane.working_plane_scene.selection_cleared.connect(selection_mgr.clear_selection) 


    # -------------------------------------------------------------------------
    # GUI → ROS (publishing user input)
    # -------------------------------------------------------------------------
    # Changes to the perspective points in the editor are published via ROS
    monitor_panel.perspective_editor.perspective_points_changed.connect(
        ros_comm.publish_four_points
    )

    # -------------------------------------------------------------------------
    # Dock Panel → Service Manager (Custom Commands)
    # -------------------------------------------------------------------------
    dock_panel.send_rgb_command.connect(service_mgr.handle_rgb_command)
    dock_panel.send_vacuum_command.connect(service_mgr.handle_vacuum_command)
    dock_panel.send_coords_command.connect(service_mgr.handle_coords_command)
    dock_panel.send_home_command.connect(service_mgr.handle_home_command)
   
    selection_mgr.selection_changed.connect(dock_panel.update_target_sliders_from_selection)

    
    main_window.logger.info("Signal connections established.")
