from setuptools import setup

package_name = 'mycobot_joint_state_publisher'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='axiomjo',
    maintainer_email='jojo.josephined@gmail.com',
    description='ngepublish topic joint states dari rasppi mycobot',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'joint_publisher_node = mycobot_joint_state_publisher.rasppi_jointpublisher_node:main',

        ],
    },
)
