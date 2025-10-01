#!/usr/bin/env python3

"""Setup file for the mycobot280pi_gui ROS 2 package."""

import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'mycobot280pi_gui'

setup(
    name=package_name,
    version='0.0.1',
    # Since the Python package has the same name as the ROS package and contains
    # sub-packages, we explicitly list them all.
    packages=find_packages(exclude=['test']),
    
    data_files=[
        # Standard ROS 2 marker file
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        # Install the package.xml file
        ('share/' + package_name, ['package.xml']),
        # Install all .launch.py files from the 'launch' directory
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='axiomjo',
    maintainer_email='jojo.josephined@gmail.com',
    description='A PyQt5 GUI for controlling the MyCobot 280 Pi robot.',
    license='Apache License 2.0',
    tests_require=['pytest'],
    # This section creates the executable that you can run with `ros2 run`
    entry_points={
        'console_scripts': [
            'gui_robot_control_node = mycobot280pi_gui.grcn_gui_main_entry:main',
        ],
    },
)
