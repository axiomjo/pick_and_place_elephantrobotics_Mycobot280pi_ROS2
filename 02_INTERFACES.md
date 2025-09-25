# ==== 02 : INTERFACES POV =======


This document outlines the architecture of the ROS2 Galactic system designed to control a MyCobot 280 Pi robot. The system integrates computer vision for object detection with motion planning and execution, managed through a graphical user interface.

---


## `camera` Namespace 📸

This namespace handles the initial, raw input from the physical camera.

### Topic: `/camera/msg_image_raw`
    * **Interface Type**: `sensor_msgs/msg/Image`
    * **Content**: A raw, unprocessed image frame with barrel distortion from the webcam.
    * **Communicating Nodes**:
        * **Publisher**: `vision_usb_cam_node`
        * **Subscriber**: `vision_undistorter_node`

---

## `vision` Namespace 👁️

This namespace is dedicated to the computer vision pipeline, from image correction to object detection.

### Topic: `/vision/msg_undistorted_image`
    * **Interface Type**: `sensor_msgs/msg/Image`
    * **Content**: An image frame corrected for lens distortion.
    * **Communicating Nodes**:
        * **Publisher**: `vision_undistorter_node`
        * **Subscribers**: `vision_perspective_transformer_node`, `gui_robot_control_node`

### Topic: `/vision/msg_top_down_image`
    * **Interface Type**: `sensor_msgs/msg/Image`
    * **Content**: A "bird's-eye view" image of the workspace after perspective correction.
    * **Communicating Nodes**:
        * **Publisher**: `vision_perspective_transformer_node`
        * **Subscribers**: `vision_object_detector_node`, `gui_robot_control_node`

### Topic: `/vision/msg_detected_objects`
    * **Interface Type**: `mycobot280pi_interfaces/msg/ManyDetectedObjects`
    * **Content**: An array of data structures, each representing a detected object with details like its ID, center point, and bounding box coordinates.
    * **Communicating Nodes**:
        * **Publisher**: `vision_object_detector_node`
        * **Subscriber**: `gui_robot_control_node`

### Topic: `/vision/msg_annotated_image`
    * **Interface Type**: `sensor_msgs/msg/Image`
    * **Content**: The top-down image with visual overlays (like bounding boxes) drawn on detected objects.
    * **Communicating Nodes**:
        * **Publisher**: `vision_object_detector_node`
        * **Subscriber**: `gui_robot_control_node`

---

## `gui` Namespace 💻

This namespace handles data flowing from the user interface to other nodes.

### Topic: `/gui/msg_four_perspective_points`
    * **Interface Type**: `mycobot280pi_interfaces/msg/Point2DArray`
    * **Content**: An array of four 2D coordinates representing the corners selected by the user for the perspective transformation.
    * **Communicating Nodes**:
        * **Publisher**: `gui_robot_control_node`
        * **Subscriber**: `vision_perspective_transformer_node`

---

## `robot` Namespace 🦾

This namespace is for publishing the robot's physical state.

### Topic: `/robot/msg_joint_angles`
    * **Interface Type**: `sensor_msgs/msg/JointState`
    * **Content**: An array of float values representing the current angle of each of the robot's joints in real-time.
    * **Communicating Nodes**:
        * **Publisher**: `robots_jointangles_publisher_node`
        * **Subscriber**: `gui_robot_control_node`

---

## `planner` Namespace 🤖

This namespace manages the logic for motion planning and task execution.

### Topic: `/planner/msg_primitive_command`
    * **Interface Type**: `mycobot280pi_interfaces/msg/SimpleCommands`
    * **Content**: A single, low-level command (e.g., move to a specific coordinate, set the vacuum pump state) for the robot to execute immediately.
    * **Communicating Nodes**:
        * **Publisher**: `planner_robot_node`
        * **Subscriber**: `robot_executor_node`

### Service: `/planner/srv_simple_command`
    * **Interface Type**: `mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure`
    * **Content**: A request-response structure for simple, blocking commands. The **request** contains a command string, and the **response** returns a boolean indicating success or failure.
    * **Communicating Nodes**:
        * **Server**: `planner_robot_node`
        * **Client**: `gui_robot_control_node`

### Action: `/planner/act_complex_command`
    * **Interface Type**: `mycobot280pi_interfaces/action/ProcessWorkspace`
    * **Content**: A goal-feedback-result structure for complex, long-running tasks. The **goal** defines the desired start and end states of objects in the workspace. The **feedback** provides progress updates (e.g., "3 of 5 objects moved"). The **result** confirms the successful completion of the entire task.
    * **Communicating Nodes**:
        * **Server**: `planner_robot_node`
        * **Client**: `gui_robot_control_node`

---

## `rviz2` Namespace 🖼️

This namespace is used specifically for broadcasting robot model data to the RViz2 visualization tool.

### Topic: `/rviz2/tf` & `/rviz2/tf_static`
    * **Interface Type**: `tf2_msgs/msg/TFMessage`
    * **Content**: These topics publish the tree of coordinate frame transformations for the robot. `/tf` handles dynamic frames that change with joint movement, while `/tf_static` handles fixed frames.
    * **Communicating Nodes**:
        * **Publisher**: `mycobot_state_publisher_node`
        * **Subscriber**: `ui_rviz2_node`
        
       
## CUSTOM INTERFACE CONTENTS
-----

### 1\. `ManyDetectedObjects.msg` 💬

This is a **message (.msg)** interface that holds an array of detected objects. It's often used for a node to publish all objects it sees in a single message.

```
# Filepath: src/mycobot280pi_interfaces/msg/ManyDetectedObjects.msg

# This part is the message definition
std_msgs/Header header
OneDetectedObject[] objects
```

-----

### 2\. `OneDetectedObject.msg` 💬

This is a **message (.msg)** interface that defines the data structure for a single detected object.

```
# Filepath: src/mycobot280pi_interfaces/msg/OneDetectedObject.msg

# This part is the message definition
int32 id
Point2D center_point
int32 width
int32 height
```

-----

### 3\. `Point2D.msg` 💬

This is a basic **message (.msg)** interface that defines a two-dimensional point.

```
# Filepath: src/mycobot280pi_interfaces/msg/Point2D.msg

# This part is the message definition
float32 x
float32 y
```

-----

### 4\. `Point2DArray.msg` 💬

This is a **message (.msg)** interface that defines an array of two-dimensional points.

```
# Filepath: src/mycobot280pi_interfaces/msg/Point2DArray.msg

# This part is the message definition
Point2D[] points
```

-----

### 5\. `SimpleCommands.msg` 💬

This is a versatile **message (.msg)** interface for sending simple robot commands.

```
# Filepath: src/mycobot280pi_interfaces/msg/SimpleCommands.msg

# This part is the message definition
string command_type

float32[] coords
float32[] joint_angles
int32 speed

int32 r
int32 g
int32 b

string[] extra_strings
float32[] extra_floats
int32[] extra_ints
```

-----

### 6\. `Mycobot280PiSimpleCommandsMadeSure.srv` 🤝

This is a **service (.srv)** interface, which defines a request-response communication pair.

```
# Filepath: src/mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure.srv

# This part is the request
float32[] coords
int32 speed
bool is_linear_mode
---
# This part is the response
bool success
string message
```

-----

### 7\. `ProcessWorkspace.action` 🚀

This is an **action (.action)** interface, which defines a goal-result-feedback communication sequence.

``` 
    # Filepath: src/mycobot280pi_interfaces/action/ProcessWorkspace.action

    # This part is the goal
    ManyDetectedObjects objects_to_move
    Point2DArray objects_target_position
    int32[] objects_target_orientation
    ---
    # This part is the result
    bool success
    string message
    ---
    # This part is the feedback
    string current_state
    OneDetectedObject current_object
```  



