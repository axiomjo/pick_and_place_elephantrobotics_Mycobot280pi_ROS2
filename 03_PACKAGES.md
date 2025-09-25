# ==== 03 : PACKAGES POV =======

## Package Summary 📦

This section outlines the custom packages in the workspace and the nodes they contain.

### 1. `mycobot280pi_interfaces` Package Overview  📦
* **Purpose**: Defines all custom message, service, and action types that all the other packages will use for communication.
* **Contents**:
    * `msg/Point2D`
    * `msg/Point2DArray`
    * `msg/ManyDetectedObjects`
    * `msg/OneDetectedObject`
    * `msg/SimpleCommands`
    * `srv/Mycobot280PiSimpleCommandsMadeSure`
    * `action/ProcessWorkspace`

---
### 2. `mycobot280pi_vision` Package Overview 🛠️ 📐 🎯
* **Purpose**: Contains all nodes responsible for image processing and computer vision tasks.
* **Nodes**:
    * `vision_undistorter_node`
    * `vision_perspective_transformer_node`
    * `vision_object_detector_node`
    
---
### 3. `mycobot280pi_robot` Package Overview 🦾🏃
* **Purpose**: Contains the core robot control and state-reporting nodes that communicate directly with MyCobot 280 Pi, pymycobot API, or the ROS 2 ecosystem. It needs to be run on the MyCobot 280 Pi.
* **Nodes**:
    * `robot_executor_node`
    * `robot_jointangles_publisher_node`

---
### 4.`mycobot280pi_planner` Package Overview 🤖
* **Purpose**: This package holds the high-level logic for autonomous operation, including planning and command dispatch.
* **Nodes**:
    * `planner_robot_node`

---
---
### 5.`mycobot280pi_gui` Package Overview 💻
* **Purpose**: Contains the central user interface node for command and control.
* **Node**:
    * `gui_robot_control_node`

---
### 6. Pre-Existing ROS 2 Tool Packages 📸 📝 🖼️
* **Nodes**:
    * `vision_usb_cam_node`
    * `mycobot_state_publisher_node`
    * `ui_rviz2_node`


## Node-Centric Package Structure

**Node Acronyms:**

  * `vision_undistorter_node` → **VUN**
  * `vision_perspective_transformer_node` → **VPTN**
  * `vision_object_detector_node` → **VODN**
  * `robot_executor_node` → **REN**
  * `robot_jointangles_publisher_node` → **RJPN**
  * `planner_robot_node` → **PRN**
  * `gui_robot_control_node` → **GRCN**

-----

## Node Breakdown before putting it in the packages
each file's responsibilities are explicitly mapped to the functionalities 

### `vision_undistorter_node` Node Breakdown 🛠️

-   **Predicted Complexity:** Short
-   **Possible Dependencies:** `rclpy`, `sensor_msgs/msg/Image`, `cv_bridge`, `OpenCV`
-   **Separation of Concerns:**
    -   `mycobot280pi_vision/vun_main_ros_node.py`: Subscribes to `/camera/msg_image_raw`, **applies the lens correction** using the provided Charuco calibration data, and publishes the result to `/vision/msg_undistorted_image`.

---

### `vision_perspective_transformer_node` Node Breakdown 📐

-   **Predicted Complexity:** Medium
-   **Possible Dependencies:** `rclpy`, `sensor_msgs/msg/Image`, `mycobot280pi_interfaces/msg/Point2DArray`, `cv_bridge`, `OpenCV`
-   **Separation of Concerns:**
    1.  `mycobot280pi_vision/vptn_main_ros_node.py`: Manages the ROS 2 interfaces. It subscribes to both `/vision/msg_undistorted_image` and `/gui/msg_four_perspective_points` and passes the data to the transformation module.
    2.  `mycobot280pi_vision/vptn_perspective_transform.py`: Contains the core OpenCV logic to **perform the perspective transform** on the image based on the four points received from the GUI.

---

### `vision_object_detector_node` Node Breakdown 🎯

-   **Predicted Complexity:** Long
-   **Possible Dependencies:** `rclpy`, `sensor_msgs/msg/Image`, `mycobot280pi_interfaces/msg/ManyDetectedObjects`, `cv_bridge`, `OpenCV`
-   **Separation of Concerns:**
    1.  `mycobot280pi_vision/vodn_main_ros_node.py`: Manages the ROS 2 interfaces. It subscribes to `/vision/msg_top_down_image`, calls the detection algorithm, and then publishes to `/vision/msg_detected_objects` and `/vision/msg_annotated_image`.
    2.  `mycobot280pi_vision/vodn_object_detection.py`: Contains the core **blob detection algorithm**. It processes the top-down image to **find object center points** and **draws bounding boxes** onto a copy of the image to create the annotated view.
    3.  `mycobot280pi_vision/vodn_message_converter.py`: Takes the raw output from the detection algorithm (e.g., a list of coordinates and box sizes) and **converts it into the `ManyDetectedObjects` message format** for publishing.

---

### `gui_robot_control_node` Node Breakdown 💻

-   **Predicted Complexity:** Very Long
-   **Possible Dependencies:** `rclpy`, `mycobot280pi_interfaces`, `sensor_msgs`, `PyQt5`
-   **Separation of Concerns:**
    1.  `grcn_main.py`: The main entry point that initializes the ROS 2 node and the PyQt application.
    2.  `grcn_gui_main_window.py`: Assembles all the GUI panels and widgets into the final application window.
    3.  `grcn_gui_camera_panel.py`: **Displays the `/vision/msg_undistorted_image` stream** and contains the logic for the **four draggable points** used for perspective correction.
    4.  `grcn_gui_working_plane.py`: The main interactive workspace. It **displays the final top-down annotated image**, renders objects for **drag-and-drop interaction**, and handles the **coordinate system transformation** (y-axis flip). It also contains the special region for the **book flipping feature**.
    5.  `grcn_gui_dock_panel.py`: Uses the object data to **crop bounding boxes** from the annotated image and displays the resulting object cutouts. It also provides controls for rotating objects before placement.
    6.  `grcn_gui_control_panel.py`: Contains all user controls, including buttons to trigger **simple commands**, the **EMERGENCY stop**, and the **refresh scene** function. It also initiates the complex command action and **displays the real-time joint angles** as bar graphs.
    7.  `grcn_pyqt_widget.py`: Defines any custom, reusable PyQt widgets, such as the joint angle bars.
    8.  `grcn_ros_communication.py`: The central ROS 2 interface. It handles **all subscriptions** (images, objects, joint states), the **publisher** for the four perspective points, the **service client** for simple commands, and the **action client** for complex commands, including processing feedback.

---

### `planner_robot_node` Node Breakdown 🤖

-   **Predicted Complexity:** Very Long
-   **Possible Dependencies:** `rclpy`, `mycobot280pi_interfaces`, `sensor_msgs`
-   **Separation of Concerns:**
    1.  `mycobot280pi_planner/prn_main_ros_node.py`: The main entry point that initializes the node and its servers.
    2.  `mycobot280pi_planner/prn_planning_logic.py`: Contains the core **Finite-State Machine (or switch-case logic)** that **breaks down complex tasks into a sequence of primitive commands**. It also manages the publisher for `/planner/msg_primitive_command`.
    3.  `mycobot280pi_planner/prn_action_server.py`: Contains the class and callbacks to handle the `/planner/act_complex_command` **action server**, including goal processing and sending feedback to the GUI.
    4.  `mycobot280pi_planner/prn_service_server.py`: Contains the class and callback to handle the `/planner/srv_simple_command` **service server** for immediate, simple commands.

---

### `robot_mycobot_joint_publisher_node` Node Breakdown 🦾

-   **Predicted Complexity:** Short
-   **Possible Dependencies:** `rclpy`, `pymycobot`, `sensor_msgs/msg/JointState`
-   **Separation of Concerns:**
    -   `mycobot280pi_robot/rmjpn_main_ros_node.py`: Contains a simple loop that repeatedly **calls the `get_angles()` function** from the pymycobot API and **publishes the result** to the `/robot/msg_joint_angles` topic for the GUI to display.

---

### `robot_executor_node` Node Breakdown 🏃

-   **Predicted Complexity:** Long
-   **Possible Dependencies:** `rclpy`, `mycobot280pi_interfaces`, `pymycobot`
-   **Separation of Concerns:**
    1.  `mycobot280pi_robot/rmen_main_ros_node.py`: The main node file. It **subscribes to `/planner/msg_primitive_command`** and delegates the received commands to the interface module.
    2.  `mycobot280pi_robot/rmen_mycobot_interface.py`: A wrapper module that **translates the primitive commands** (e.g., "move_to_coords", "set_pump") into specific **`pymycobot` API calls** to control the physical robot.
    3.  `mycobot280pi_robot/rmen_robot_state_manager.py`: A module for tracking the robot's current state (e.g., `busy`, `idle`, `error`) to prevent command conflicts and handle errors gracefully.

---

## Package Skeleton
Modules are prefixed with the acronym of the node they serve.

### 1\. `mycobot280pi_interfaces` Package 📦


```
    └── mycobot280pi_vision/
        ├── launch/
        ├── resource/                   # For camera calibration files, etc.
        ├── mycobot280pi_vision/
        │   ├── __init__.py
        │   ├── vun_main_ros_node.py
        │   ├── vptn_main_ros_node.py
        │   ├── vptn_perspective_transform.py
        │   ├── vodn_main_ros_node.py
        │   ├── vodn_object_detection.py
        │   └── vodn_message_converter.py
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```

### 2\. `mycobot280pi_vision` Package 🛠️ 📐 🎯


```
    └── mycobot280pi_vision/
        ├── launch/
        ├── resource/                   # For camera calibration files, etc.
        ├── mycobot280pi_vision/
        │   ├── __init__.py
        │   ├── vun_main_ros_node.py
        │   ├── vptn_main_ros_node.py
        │   ├── vptn_perspective_transform.py
        │   ├── vodn_main_ros_node.py
        │   ├── vodn_object_detection.py
        │   └── vodn_message_converter.py
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```


-----

### 3\. `mycobot280pi_robot` Package 🦾🏃

both nodes interact with the same `pymycobot` API.

```
    ├── mycobot280pi_robot/
        ├── launch/
        ├── mycobot280pi_robot/
        │   ├── __init__.py
        │   ├── ren_main_ros_node.py
        │   ├── ren_mycobot_interface.py
        │   ├── ren_robot_state_manager.py
        │   └── rfjpn_main_ros_node.py
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```
---

### 4\. `mycobot280pi_planner` Package 🤖

The planner's logic is separated into a dedicated module.

```
    ├── mycobot280pi_planner/
        ├── launch/
        ├── mycobot280pi_planner/
        │   ├── __init__.py
        │   ├── prn_main_ros_node.py
        │   ├── prn_planning_logic.py
        │   ├── prn_action_server.py
        │   └── prn_service_server.py
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```

-----

### 5\. `mycobot280pi_gui` Package 💻

The GUI maintains a clear separation between the user interface, ROS 2 communication, and the main application entry point.

```
    ├── mycobot280pi_gui/
        ├── launch/                     # For ROS 2 launch files
        ├── resource/                   # For non-code assets like .ui files
        ├── mycobot280pi_gui/
        │   ├── __init__.py
        │   ├── grcn_main.py
        │   ├── grcn_gui_main_window.py
        │   ├── grcn_gui_camera_panel.py
        │   ├── grcn_gui_working_plane.py
        │   ├── grcn_gui_dock_panel.py
        │   ├── grcn_gui_control_panel.py
        │   ├── grcn_pyqt_widget.py
        │   └── grcn_ros_communication.py
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```


