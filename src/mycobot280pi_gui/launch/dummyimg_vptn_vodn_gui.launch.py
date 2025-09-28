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
    
        # dummy_circle_n_squares_img_node
        Node(
            package='mycobot280pi_dummy',
            executable='dummy_circle_n_squares_img_node',
            name='dummy_circle_n_squares_img_node',
            remappings=[
                ('/dummy/undistorted600x600', '/vision/msg_undistorted_image'),
            ],

            
                
        ),

        # Vision Perspective Transformer Node
        Node(
            package='mycobot280pi_vision',
            executable='vision_perspective_transform_node',
            name='vision_perspective_transform_node',
            output='screen',
            parameters=[{'output_size': 600}]
        ),
        
        #vision object detector node
        Node(
            package='mycobot280pi_vision',
            executable='vision_object_detector_node',
            name='vision_object_detector_node',
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
