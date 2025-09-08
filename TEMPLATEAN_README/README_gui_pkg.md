5. gui_robot_control_node Node 💻
"Ciri Khas": The Commander Role: User Interface Function: The user interface for monitoring and controlling the robot. It displays live data, lets users set perspective points, displays the final detection results, provides manual controls, and initiates complex tasks. Expected Task:

Display image streams, final processed image, and object cutouts

Allow interactive perspective editing

Publish points to trigger a one-time scene processing

Display the robot's current joint angles and Cartesian coordinates.

Initiate robot planner and displays real time report

Node Communication
Subscribers
/vision/undistorted_image Topic

Interface Type: sensor_msgs/msg/Image
Details: Receives from vision_undistorter_node.
/vision/corrected_image Topic

Interface Type: sensor_msgs/msg/Image
Details: Receives from vision_perspective_transformer_node.
/vision/detected_objects Topic

Interface Type: mycobot280pi_interfaces/msg/ManyDetectedObjects
Details: Receives from vision_object_detector_node.
/robot/joint_states Topic

Interface Type: sensor_msgs/msg/JointState
Details: Receives from robot_mycobot_joint_publisher_node.
Publishers
/vision/perspective_points Topic

Interface Type: mycobot280pi_interfaces/msg/Point2DArray
Details: Publishes to vision_perspective_transformer_node.
/planner/manual_commands Topic

Interface Type: mycobot280pi_interfaces/msg/SimpleCommands
Details: Publishes to planner_robot_node.
Service Clients
/planner/set_coords Service
Interface Type: mycobot280pi_interfaces/srv/Mycobot280PiSetCoordsMadeSure
Details: Sends requests to planner_robot_node.
Action Clients
/planner/process_workspace Action
Interface Type: mycobot280pi_interfaces/action/ProcessWorkspace
Details: Sends requests to planner_robot_node.

