# Interface type: mycobot280pi_interfaces/msg/ManyDetectedObjects
# Filepath: src/mycobot280pi_interfaces/msg/ManyDetectedObjects.msg
# Uses: OneDetectedObject (as objects[])
# Used in: /vision/detected_objects topic, planner_robot_node, gui_robot_control_node
#ManyDetectedObjects.msg

std_msgs/Header header
DetectedObject[] objects
