from launch import LaunchDescription
from launch_ros.actions import Node

import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():


    # 1. Get the package share directory
    pkg_share_path = get_package_share_directory('mycobot280pi_vision')
    
    # 2. Construct the full path to the file
    camera_info_file_path = os.path.join(pkg_share_path, 'hardwareconfig', 'camera_calibration.yaml')


    return LaunchDescription([
    
        # vision_usb_cam_node
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='vision_usb_cam_node',
            remappings=[
                ('/image_raw', '/camera/msg_image_raw'),
            ],

            # This handles all the '-p' arguments
            parameters=[{
                'video_device': '/dev/video0',
                'camera_name': 'my_camera',
                'camera_info_url': 'file://' + camera_info_file_path,
            }]
                
        ),
        # Vision Undistorter Node
        Node(
            package='mycobot280pi_vision',
            executable='vision_undistorter_node',
            name='vision_undistorter_node',
            output='screen',
            parameters=[{'camera_info_file': camera_info_file_path}]
        ),
        # Vision Perspective Transformer Node
        Node(
            package='mycobot280pi_vision',
            executable='vision_perspective_transform_node',
            name='vision_perspective_transform_node',
            output='screen',
            parameters=[{'output_size': 600}]
        ),
        # GUI Robot Control Node
        Node(
            package='mycobot280pi_gui',
            executable='gui_robot_control_node',
            name='gui_robot_control_node',
            output='screen'
        ),
    ])
