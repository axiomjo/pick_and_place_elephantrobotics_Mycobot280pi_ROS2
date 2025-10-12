from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, TextSubstitution # Import yang diperlukan
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # ----------------------------------------------------
    # 1. Deklarasi Launch Argument untuk Port Video
    # ----------------------------------------------------
    # Kita akan meminta pengguna memasukkan NOMOR port video (misal: 2 untuk /dev/video2)
    video_port_arg = DeclareLaunchArgument(
        'X',
        default_value=TextSubstitution(text='0'), # Nilai default jika pengguna tidak memasukkan apa-apa
        description='Nomor port video (X) untuk /dev/videoX. Defaultnya adalah 0.'
    )

    # ----------------------------------------------------
    # 2. Konfigurasi Path Device dari Input
    # ----------------------------------------------------
    # Ambil nilai yang dimasukkan oleh pengguna
    video_port_num = LaunchConfiguration('X')
    
    # Buat string "/dev/videoX" dengan menggabungkan teks dan input pengguna
    video_device_path = [TextSubstitution(text='/dev/video'), video_port_num]


    # ----------------------------------------------------
    # 3. Setup Konfigurasi Tambahan (sama seperti sebelumnya)
    # ----------------------------------------------------
    pkg_share_path = get_package_share_directory('mycobot280pi_vision')
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
                'video_device': video_device_path,
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
            output='screen',
            emulate_tty=True
        ),
        
        # planner robot node
        Node(
            package='mycobot280pi_planner',
            executable='planner_robot_node',
            name='planner_robot_node',
            output='screen',
            emulate_tty=True
        ),
        
        
    ])
