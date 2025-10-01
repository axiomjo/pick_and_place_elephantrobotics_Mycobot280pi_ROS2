"""
grcn_signal_connector.py - Centralizes all Qt signal-slot connections.

This module connects:
- ROS facade signals → GUI widgets.
- Control panel buttons → GUI managers.
- Peer widget interactions (dock ↔ working plane, etc.).
"""

def connect_signals(main_window):
    """
    Wires up all signals and slots for the application.

    :param main_window: Reference to the QMainWindow instance (with managers + widgets).
    """

    # -------------------------------------------------------------------------
    # ROS → GUI (data updates)
    # -------------------------------------------------------------------------
    main_window.ros_comm.detected_objects_received.connect(main_window.cache_detected_objects)
    main_window.ros_comm.annotated_image_received.connect(main_window.cache_annotated_image)
    main_window.ros_comm.undistorted_image_received.connect(
        main_window.camera_panel.perspective_editor.update_frame
    )
    main_window.ros_comm.annotated_image_received.connect(main_window.camera_panel.update_camera_view)
    main_window.ros_comm.joint_state_received.connect(main_window.joint_angles_display_panel.update_joint_display)

    # -------------------------------------------------------------------------
    # Control Panel → Managers
    # -------------------------------------------------------------------------
    main_window.control_panel.analyze_btn.clicked.connect(
        main_window.action_mgr.start_action
    )
    main_window.control_panel.emergency_btn.clicked.connect(
        main_window.action_mgr.cancel_action
    )
    main_window.control_panel.send_btn.clicked.connect(
        main_window.service_mgr.send_service_request
    )
    main_window.control_panel.reset_btn.clicked.connect(
        main_window.plane_mgr.reset_plane
    )
    main_window.control_panel.add_object_btn.clicked.connect(
        main_window.plane_mgr.add_new_objects_from_cutouts
    )
    main_window.control_panel.delete_btn.clicked.connect(
        main_window.plane_mgr.delete_selected
    )

    # -------------------------------------------------------------------------
    # Working Plane → Selection Manager
    # -------------------------------------------------------------------------
    main_window.working_plane.working_plane_scene.selectionChanged.connect(
        main_window.selection_mgr.update_status_bar_with_selection
    )

    # -------------------------------------------------------------------------
    # Dock Panel → Working Plane
    # -------------------------------------------------------------------------
    main_window.dock_panel.rotation_slider.valueChanged.connect(
        main_window.working_plane.set_selected_items_rotation
    )

    # -------------------------------------------------------------------------
    # Control Panel (rotation) → Working Plane
    # -------------------------------------------------------------------------
    main_window.control_panel.rotate_clockwise_btn.clicked.connect(
        main_window.working_plane.rotate_clockwise
    )
    main_window.control_panel.rotate_counter_clockwise_btn.clicked.connect(
        main_window.working_plane.rotate_counter_clockwise
    )

    # -------------------------------------------------------------------------
    # Camera Panel → ROS (perspective points)
    # -------------------------------------------------------------------------
    main_window.camera_panel.perspective_editor.perspective_points_changed.connect(
        main_window.ros_comm.publish_four_points
    )
    
    

    # -------------------------------------------------------------------------
    # Dock Panel → Service Manager (Service Commands NEW)
    # -------------------------------------------------------------------------
    main_window.dock_panel.send_rotation_command.connect(
        main_window.service_mgr.handle_rotation_command
    )
    main_window.dock_panel.send_rgb_command.connect(
        main_window.service_mgr.handle_rgb_command
    )
    main_window.dock_panel.send_vacuum_command.connect(
        main_window.service_mgr.handle_vacuum_command
    )
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

