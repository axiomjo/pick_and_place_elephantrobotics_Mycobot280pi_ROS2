from setuptools import setup

import os
from glob import glob

package_name = 'mycobot280pi_dummy'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name,'mycobot280pi_dummy_robot'],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='axiomjo',
    maintainer_email='jojo.josephined@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'dummy_gui_robot_control_node = mycobot280pi_dummy.dummy_gui_robot_control_node:main',
            'd2ummy_gui_robot_control_node = mycobot280pi_dummy.dummy_gui_robot_control_node_2:main',
            'dummy_circle_n_squares_img_node = mycobot280pi_dummy.dummy_generated_600x600oixel_img:main',
            'dummy_raw_webcam = mycobot280pi_dummy.dummy_singlephoto_publisher_img:main',
            'dummy_executor_node = mycobot280pi_dummy_robot.ren_main_ros_node:main',
            
        
            
        ],
    },
)
