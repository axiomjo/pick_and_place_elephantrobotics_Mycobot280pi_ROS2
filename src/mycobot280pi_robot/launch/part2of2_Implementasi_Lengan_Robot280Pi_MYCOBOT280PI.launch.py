import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # 1. Get package share directory
    pkg_share_path = get_package_share_directory('mycobot280pi_urdf')

    # 2. Path to URDF (xacro file)
    xacro_file_path = os.path.join(pkg_share_path, 'urdf','mycobot_280_pi', 'mycobot280pi_with_pump_edited_to_match_mycobot280pi_urdf.urdf')

    # 3. Expand the xacro into URDF
    robot_description_content = Command(['xacro',' ', xacro_file_path])

    # ----------------------------------------------------------------------
    # Return LaunchDescription inline (Style A)
    # ----------------------------------------------------------------------
    return LaunchDescription([

        # Robot Executor Node
        Node(
            package='mycobot280pi_robot',
            executable='robot_executor_node',
            name='robot_executor_node',
            output='screen',
            emulate_tty=True
        ),

        # Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher_node',
            output='screen',
            parameters=[{'robot_description': robot_description_content}]
        ),

    ])

