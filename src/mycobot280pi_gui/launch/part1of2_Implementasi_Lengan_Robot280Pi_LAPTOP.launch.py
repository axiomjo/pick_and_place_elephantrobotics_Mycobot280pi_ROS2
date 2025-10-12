from launch import LaunchDescription
from launch_ros.actions import Node
import os
import subprocess
import re
from ament_index_python.packages import get_package_share_directory

# --- FUNGSI BARU UNTUK MENCARI PORT VIDEO ---
def find_webcam_device(target_name_part="WEB CAM"):
    """
    Mengeksekusi 'v4l2-ctl --list-devices' dan mencari device path 
    (misalnya /dev/video2) yang terasosiasi dengan nama kamera.
    """
    try:
        # Jalankan v4l2-ctl --list-devices
        result = subprocess.run(
            ['v4l2-ctl', '--list-devices'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        output = result.stdout
    except FileNotFoundError:
        print("Error: Command 'v4l2-ctl' not found. Pastikan 'v4l-utils' sudah terinstall.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error saat mengeksekusi v4l2-ctl: {e}")
        return None

    # Parsing output
    # Pola untuk mencari nama kamera dan path device. 
    # Kita cari blok yang mengandung target_name_part, lalu ambil /dev/videoX pertama.
    
    # Memisahkan output menjadi blok-blok per device
    device_blocks = output.strip().split('\n\n')

    for block in device_blocks:
        if target_name_part.lower() in block.lower():
            # Jika nama yang dicari (misalnya 'WEB CAM') ditemukan, 
            # cari path /dev/videoX pertama di blok tersebut.
            
            # Pola regex untuk mencari path /dev/videoX
            match = re.search(r'(/dev/video\d+)', block)
            if match:
                print(f"Ditemukan device '{match.group(1)}' untuk kamera '{target_name_part}'.")
                return match.group(1)
                
    print(f"Peringatan: Tidak ditemukan device yang cocok dengan nama '{target_name_part}'. Menggunakan '/dev/video0' sebagai fallback.")
    return "/dev/video0" # Fallback jika tidak ditemukan


def generate_launch_description():

    webcam_device_path = find_webcam_device(target_name_part="WEB CAM")
    
    if webcam_device_path is None:
        # Jika v4l2-ctl gagal, kamu bisa memilih untuk menghentikan launch atau menggunakan default
        raise RuntimeError("Gagal menemukan device webcam. Pastikan 'v4l2-ctl' berfungsi.")


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
                'video_device': webcam_device_path,
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

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
        ),
        
        
    ])
