[LAST EDITED: 7 SEP 2025 04:09]

# Implementasi_MyCobot280pi_ROS2

branch `FINAL_VERSION`
this branch will be the one with clear patterns.    

--- 

# === HOW TO RUN THIS SYSTEM ===

part not written yet
---

# 📌 What to Code First (MVP Plan)

* **Step 1: Get the Robot Moving Manually.**
  
  * Goal: Be able to send basic movement commands to the robot and see its state.
  * Tasks:
    * ✅ **Complete:** Install ROS 2 Galactic and test MyCobot's movement.
    * ✅ **Complete:** Verify LAN communication with the MyCobot 280 Pi.
    * Build the robot description file and put it in `urdf` directory inside the robot package.
    * Build the `robot_mycobot_executor_node` to receive simple commands and control the robot via the `pymycobot` API.
    * Test manual commands by publishing to `/planner/manual_commands`.

* **Step 2: Get the Camera Feed Working.**
  
  * Goal: Display the camera feed in the GUI.
  * Tasks:
    * Use `usb_cam` to capture and display a video feed.
    * Generate the necessary camera calibration file for `vision_undistorter_node` using charuco and a python file. just do it once, and put it inside `hardware_specifics` inside the vision package.
    * Build the `vision_undistorter_node` to correct lens distortion.
    * Build the `gui_robot_control_node` with a basic video display widget to subscribe to `/vision/undistorted_image`.

* **Step 3: Implement Object Detection and Perspective Transform.**
  
  * Goal: Accurately identify an object's location and publish it to the planner.
  * Tasks:
    * Build the `vision_perspective_transformer_node` to perform the perspective transform.
    * Build the `vision_object_detector_node` to run a blob detection algorithm.
    * Ensure the GUI can publish perspective points to `/vision/perspective_points`.
    * Verify that `/vision/detected_objects` is correctly publishing the object data.

* **Step 4: Create the Planner & Executor Loop.**
  
  * Goal: Make the robot move to a detected object and perform a simple pick action.
  * Tasks:
    * Build the core `planner_robot_node`.
    * Have the `planner_robot_node` subscribe to `/vision/detected_objects`.
    * Implement the planning logic to receive object coordinates and publish commands to `/planner/commands`.
    * Write the logic in `robot_mycobot_executor_node` to handle simple vacuum pump on/off commands.

* **Step 5: Full Automated Pick-and-Place Cycle.**
  
  * Goal: Automate the entire process from detection to dropping the object.
  * Tasks:
    * Add the necessary logic to `planner_robot_node` to handle the full sequence:
      1. Move arm to object.
      2. Activate vacuum pump.
      3. Lift and move object to a drop zone.
      4. Release object.
    * Integrate the `ProcessWorkspace` action server and client so the GUI can initiate a full cycle.
    * Test the end-to-end functionality to ensure the robot can reliably pick up and place an object.

---

trus:

- gdocs & pdf buku TA,
- slides presentasi,
- poster,
- artikel ilmiah
  (ini apalagi yg kurang? mumet gw baca panduan BAA)

---

Project Milestones & Progress

## Important Deadlines:

* **PRASEM DAFTAR (P_DAFTAR):** September 9, 2025
* **PRASEM ACT (P_AKTUAL):** September 15-19, 2025 (Actual date will be updated :>)
* **DOSEN ESTETIK (D_ESTETIK):** September 25, 2025
* **SEMINAR DAFTAR (S_DAFTAR):** October 7, 2025
* **SEMINAR AKTUAL (S_AKTUAL):** October 13-17, 2025
* **BUKU BAA (BUKU_BAA):** November 7, 2025
* **SYARAT YUDIS (SYAR_YUDI):** November 10, 2025
* **YUDISIUM (YUDISIUM):** November 12, 2025

---

# ==== NODE COMMUNICATION =======

### **1. `vision_usb_cam_node`** Node 📸  (ROS2 PRE-BUILT PKG)

**"Ciri Khas":** The Raw Image Publisher
**Role:** Publisher
**Function:** Captures raw, barrel-distorted images from the webcam using the ROS2's preexisting `usb_cam` package. It's the main image source for the pipeline.
**Expected Task:** Continuously stream raw images from the webcam.

#### Node Parameter Configuration

1. `video_device` Parameter
   * **Interface Type:** `String`
   * **Details:** This is a mandatory parameter that specifies the path to your USB camera device. A common value is /dev/video0
  
2. `camera_name` Parameter
   * **Interface Type:** `String`
   * **Details:** This parameter sets the name of the camera, which is used to define its frame ID in the ROS TF tree.
      

```

THIS WAS MY SUCCESFULL ATEMPT. BLOM SESUAI SAMA DESAIN TERBARU

   --ros-args -p camera_info_url:="file:///home/axiomjo/lab_robotik/eksperimental/ws_ROS2_mycobot280pi/src/CAM_object_detect/my_camera_capture/hardware_specifics/camera_calibration.yaml" -p camera_name:="my_camera" -p video_device:="/dev/video0"

janlup 

v4l2-ctl --list-devices 

buat tau param -p video_device:="/dev/APAAAAAINII"  kadang sering ganti2 soalnya.


   
```
#### Node Communication

##### Publishers

1. `/camera/image_raw` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_undistorter_node`.

---

### **2. `vision_undistorter_node`**  Node 🛠️

**"Ciri Khas":** The Barrel Distortion Fixer
**Role:** Subscriber & Publisher
**Function:** Subscribes to `/camera/image_raw`, applies lens correction, and publishes a cleaner, undistorted image stream.
**Expected Task:** Provide undistorted images for downstream nodes.

#### Node Parameter Configuration

1. `camera_info_url` Parameter
   * **Interface Type:** `String`
   * **Details:** This parameter should be filled with the absolute path to a YAML file containing the camera's intrinsic calibration data from `camera_calibration.yaml`, which was generated from running the python script `charuco_calibration_file.py` inside `hardware_specifics`directory inside the vision package.  This file is used by the node to correct lens distortion in the image stream.

```
   INI JUGA PAKE ACARA KUDU ABSOLUTE FILE PATH, GIMANA ATUH KLO AKU PINDAH ALAT. LAUNCHFILENYA GMN COBA
   
   --ros-args -p camera_info_file:="/home/axiomjo/lab_robotik/eksperimental/ws_ROS2_mycobot280pi/src/CAM_object_detect/my_camera_capture/hardware_specifics/camera_calibration.yaml"
   
```

#### Node Communication

##### Subscribers

1. `/camera/image_raw` Topic
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   
   * **Details:** Receives from `vision_usb_cam_node`.
     
##### Publishers

1. `/vision/undistorted_image` Topic
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_perspective_transformer_node` and `gui_robot_control_node`.

---

### **3. `vision_perspective_transformer_node`** Node 📐

**"Ciri Khas":** The Perspective Aligner
**Role:** Subscriber & Publisher
**Function:** Listens for perspective points from the GUI and the latest undistorted image, performs a perspective transform, and publishes the corrected image.
**Expected Task:** Transform the image based on user-selected points and publish the result.

#### Node Communication

##### Subscribers

1. `/vision/undistorted_image` Topic
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_undistorter_node`.

2. `/vision/perspective_points` Topic
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/Point2DArray`
   
   * **Details:** Receives from `gui_robot_control_node`.
     
##### Publishers

1. `/vision/corrected_image` Topic
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_object_detector_node` and `gui_robot_control_node`.

---

### **4. `vision_object_detector_node`** Node 🎯

**"Ciri Khas":** The Finder
**Role:** Subscriber & Publisher
**Function:** Subscribes to the perspective-corrected image, runs blob detection algorithm, and publishes detected object data and the image for the GUI.
**Expected Task:** Detect objects in the corrected image and publish results.

#### Node Communication

##### Subscribers

1. `/vision/corrected_image` Topic
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   
   * **Details:** Receives from `vision_perspective_transformer_node`.
     
##### Publishers

2. `/vision/detected_objects` Topic
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
   * **Details:** Publishes to `planner_robot_node` and `gui_robot_control_node`.

---

### **5. `gui_robot_control_node`** Node 💻

**"Ciri Khas":** The Commander
**Role:** User Interface
**Function:** The user interface for monitoring and controlling the robot. It displays live data, lets users set perspective points, displays the final detection results, provides manual controls, and initiates complex tasks.
**Expected Task:**

* Display image streams, final processed image, and object cutouts

* Allow interactive perspective editing

* Publish points to trigger a one-time scene processing

* Display the robot's current joint angles and Cartesian coordinates.

* Initiate robot planner and displays real time report
  
#### Node Communication
  
##### Subscribers
1. `/vision/undistorted_image` Topic
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_undistorter_node`.

2. `/vision/corrected_image` Topic
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_perspective_transformer_node`.

3. `/vision/detected_objects` Topic
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
   * **Details:** Receives from `vision_object_detector_node`.

4. `/robot/joint_states` Topic
   
   * **Interface Type:** `sensor_msgs/msg/JointState`
   * **Details:** Receives from `robot_mycobot_joint_publisher_node`.

   
##### Publishers

1. `/vision/perspective_points` Topic
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/Point2DArray`
   * **Details:** Publishes to `vision_perspective_transformer_node`.

2. `/planner/manual_commands` Topic
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
   
   * **Details:** Publishes to `planner_robot_node`.
     
##### Service Clients

1. `/planner/set_coords` Service
   
   * **Interface Type:** `mycobot280pi_interfaces/srv/Mycobot280PiSetCoordsMadeSure`
   
   * **Details:** Sends requests to `planner_robot_node`.
     
##### Action Clients

1. `/planner/process_workspace` Action
   
   * **Interface Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`
   * **Details:** Sends requests to `planner_robot_node`.

---

### **6. `planner_robot_node`** Node 🤖

**"Ciri Khas":** The Robot Planner
**Role:** Action Server, Service Server, Command Dispatcher
**Function:** Plan and execute a sequence of robot actions.
Allow both manual movement via service calls and automated planning via actions.
**Expected Task:** Plan and execute a sequence of robot actions and report progress back to the GUI.

#### Node Communication

##### Subscribers

1. `/vision/detected_objects` Topic
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
   
   * **Details:** Receives from `vision_object_detector_node`.
   
   
1. `/planner/manual_commands` Topic
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
   
   * **Details:** Receives from `vision_object_detector_node`.
   

     
##### Publishers

1. `/planner/commands` Topic
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
   
   * **Details:** Publishes to `robot_mycobot_executor_node`.
     
##### Service Server

1. `/planner/set_coords` Service
   
   * **Interface Type:** `mycobot280pi_interfaces/srv/Mycobot280PiSetCoordsMadeSure`
   
   * **Details:** Receives requests from `gui_robot_control_node`.
     
##### Action Server

1. `/planner/process_workspace` Action
   
   * **Interface Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`
   * **Details:** Receives requests from `gui_robot_control_node`.

---

### **7. `robot_mycobot_joint_publisher_node`** Node 🦾

**"Ciri Khas":** The Robot Joint Reporter
**Role:** Publisher
**Function:** Publishes the robot’s joint states for GUI visualization and monitoring.
**Expected Task:** Continuously report joint state.

#### Node Communication

##### Publishers

1. `/robot/joint_states` Topic
   * **Interface Type:** `sensor_msgs/msg/JointState`
   * **Details:** Publishes to `gui_robot_control_node`.

---

### **8. `robot_mycobot_executor_node`** Node🏃

**"Ciri Khas":** The Command Executor inside the actual robot
**Role:** MyCobot pymycobot API Executor
**Function:** Translates commands to ElephantRobotics'  pymycobot API calls in the robot.
**Expected Task:** Perform robot actions as commanded.

#### Node Communication

##### Subscribers

1. `/planner/commands` Topic
   * **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
   * **Details:** Receives from `planner_robot_node`.

---

### **9. `ui_rviz2_node`** Node 🖼️ (ROS2 PRE-BUILT PKG)

**"Ciri Khas":** The Extra Visualizer
**Role:** Visualization Tool
**Function:** Subscribes to a variety of topics to display a complete 3D visualization of the robot using the ROS2's preexisting `rviz2` package
**Expected Task:** Display robot and scene data for monitoring.

#### Node Communication

##### Subscribers

1. `/rviz2/tf_static` Topic
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** Publishes the static transforms for the robot. These are the fixed relationships between a robot's links and are defined by the URDF. 
     
2. `/rviz2/tf` Topic
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** Receives from `mycobot_state_publisher_node`.

---

### **10. `mycobot_state_publisher_node`** Node 📝 (ROS2 PRE-BUILT PKG)

**"Ciri Khas":** The State Broadcaster
**Role:** Publisher
**Function:** Publishes the robot’s internal state for rviz2 visualization using ROS2's preexisting  `robot_state_publisher` package.
**Expected Task: Broadcast robot state for rviz2.

#### Node Parameter Configuration
1. `robot_description` Parameter
   * **Interface Type:** `String`
   * **Details:** This parameter should be filled with  MyCobot290Pi robot's entire model in the Unified Robot Description Format (URDF). This is an example of it in my machine
   
```
I NEED A LAUNCH FILE BUT DUNNO HOW TO xacro BEFORE PUTTING IT IN PARAM.

   XACROED=$(xacro "/home/axiomjo/lab_robotik/eksperimental/ws_ROS2_mycobot280pi/install/mycobot_description/share/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi_with_pump.urdf" )

ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="${XACROED}"
```
 

#### Node Communication

##### Publishers

1. `/rviz2/tf_static` Topic
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** Publishes the static transforms for the robot. These are the fixed relationships between a robot's links and are defined by the URDF. 
   
2. `/rviz2/tf` Topic
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** This topic publishes the dynamic transforms of the robot, which are the transforms that change based on the joint states.

---

# ===== INTERFACES FOR MESSAGES, SERVICES, ACTIONS ====

[last editede: 6 Sep 2025 16:48]

`/camera` Namespace
This namespace is used for raw image data from the camera.

1. **`/camera/image_raw`**
   
        **Interface Type:** `sensor_msgs/msg/Image`
               **Publisher:** `vision_usb_cam_node`📸
           **Subscriber:** `vision_undistorter_node`🛠️

---

### `/vision` Namespace

This namespace is for all the processed image and object detection data.

1. **`/vision/undistorted_image`**
           **Interface Type:** `sensor_msgs/msg/Image`
           **Publisher:** `vision_undistorter_node`🛠️
           **Subscriber:** `vision_perspective_transformer_node`, 📐`gui_robot_control_node`💻
2. **`/vision/corrected_image`**
           **Interface Type:** `sensor_msgs/msg/Image`
           **Publisher:** `vision_perspective_transformer_node`📐
           **Subscriber:** `vision_object_detector_node`🎯, `gui_robot_control_node`💻
3. **`/vision/perspective_points`**
           **Interface Type:** `mycobot280pi_interfaces/msg/Point2DArray`
           **Publisher:** `gui_robot_control_node`💻
           **Subscriber:** `vision_perspective_transformer_node`📐
4. **`/vision/detected_objects`**
           **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
           **Publisher:** `vision_object_detector_node`🎯
           **Subscriber:** `planner_robot_node`🤖, `gui_robot_control_node`💻

---

### `/robot` Namespace

This namespace contains topics related to the physical robot's state and general commands.


1. **`/robot/joint_states`**
           **Interface Type:** `sensor_msgs/msg/JointState`
           **Publisher:** `robot_mycobot_joint_publisher_node`🦾
           **Subscriber:** `gui_robot_control_node`💻
           
---

### `/planner` Namespace

This namespace is used for all communication with the robot's planning node.

1. **`/planner/commands`** (Topic)
           **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
           **Publisher:** `planner_robot_node`🤖
           **Subscriber:** `robot_mycobot_executor_node`🏃
2. **`/planner/set_coords`** (Service)
           **Interface Type:** `mycobot280pi_interfaces/srv/Mycobot280PiSetCoordsMadeSure`
           **Client:** `gui_robot_control_node`💻
           **Server:** `planner_robot_node`🤖
3. **`/planner/process_workspace`** (Action)
           **Interface Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`        
           **Client:** `gui_robot_control_node`💻
           **Server:** `planner_robot_node`🤖
4. **`/planner/manual_commands`**
           **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
           **Publisher:** `gui_robot_control_node`💻
           **Subscriber:** `planner_robot_node`🤖

---

### `/rviz2` Namespace

This namespace is used for all the extra 3d visualization using rviz2.

1. **`/rviz2/tf_static`** (Topic)
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** Publishes the static transforms for the robot. These are the fixed relationships between a robot's links and are defined by the URDF. 
   
2. **`/rviz2/tf`** (Topic)
           **Interface Type:** `tf2_msgs/msg/TFMessage`
           **Publisher:** `mycobot_state_publisher_node`📝
           **Subscriber:** `ui_rviz2_node`🖼️


# ===== PACKAGEs TO BE BUILT =======

### 1. `mycobot280pi_interfaces` Package Overview  📦

 This package contains no nodes. It holds the custom message, service, and action definitions that all the other packages will use for communication.

--- 

### 2. `mycobot280pi_vision` Package Overview 🛠️ 📐 🎯

This package is for the entire vision pipeline. All nodes related to image capture, processing, and object detection belong here.

1. **`vision_undistorter_node`** - The Barrel Distortion Fixer
2. **`vision_perspective_transformer_node`** - The Perspective Aligner
3. **`vision_object_detector_node`** - The Finder

---

### 3. `mycobot280pi_robot` Package Overview 🦾📝🏃

This package contains the core robot control and state-reporting nodes that communicate directly with MyCobot 280 Pi or the ROS 2 ecosystem. It needs to be run on the MyCobot 280 Pi.

1. **`robot_mycobot_joint_publisher_node`** - The Robot Joint Reporter
2. **`robot_mycobot_executor_node`** - The Command Executor

---

### 4.`mycobot280pi_planner` Package Overview 🤖

This package holds the high-level logic for autonomous operation, including planning and command dispatch.

1. **`planner_robot_node`** - The Robot Planner

---

### 5.`mycobot280pi_gui` Package Overview 💻

This is the dedicated package for your user interface.

1. **`gui_robot_control_node`** - The Commander

---

### 6. Pre-Existing ROS 2 Tool Packages 📸 🖼️

1. **`vision_usb_cam_node`** - The Raw Image Publisher from `usb_cam`
2. **`ui_rviz2_node`** - The Extra Visualizer from `rviz`
3. **`mycobot_state_publisher_node`** - The State Broadcaster from `robot_state_publisher` 

--- 

# ===== NODE DEPENDENCIES AND PARTS ======

[last edited 6 Sep 2025 15:22]

### `vision_undistorter_node` Node Breakdown 🛠️

- **Predicted Complexity:** Short

- **Possible Dependencies:** `rclpy`, `sensor_msgs/msg/Image`, `cv_bridge`, `OpenCV`

- **Separation of Concerns:**
  
  - `mycobot280pi_vision/vun_main_ros_node.py` (The main ROS node file)

---

### `vision_perspective_transformer_node` Node Breakdown 📐

- **Predicted Complexity:** Medium

- **Possible Dependencies:** `rclpy`, `sensor_msgs/msg/Image`, `mycobot280pi_interfaces/msg/Point2DArray`, `cv_bridge`, `OpenCV`

- **Separation of Concerns:**
  
  1. `mycobot280pi_vision/vptn_main_ros_node.py`(The main ROS node file)
  
  2. `mycobot280pi_vision/vptn_perspective_transform.py`(The module with the core OpenCV transformation algorithm)

---

### `vision_object_detector_node` Node Breakdown 🎯

- **Predicted Complexity:** Long

- Possible Dependencies:** `rclpy`, `sensor_msgs/msg/Image`, `mycobot280pi_interfaces/msg/ManyDetectedObjects`, `cv_bridge`, `OpenCV`

- **Separation of Concerns:**
  
  1. `mycobot280pi_vision/vodn_main_ros_node.py`(The main ROS node file)
  
  2. `mycobot280pi_vision/vodn_object_detection.py`(The module with the vision algorithm)
  
  3. `mycobot280pi_vision/vodn_message_converter.py` (The module to convert data types to ROS messages)

---

### `gui_robot_control_node` Node Breakdown 💻

- **Predicted Complexity:** Very Long

- **Possible Dependencies:** `rclpy`, `mycobot280pi_interfaces`, `sensor_msgs`, `PyQt5`

- **Separation of Concerns:**
  
  1. `mycobot280pi_gui/grcn_main.py`(The main entry point)
  
  2. `mycobot280pi_gui/grcn_pyqt_gui_app.py` (The main GUI window and layout with PyQt)
  
  3. `mycobot280pi_gui/grcn_ros_communication.py`(The ROS communication class)
  
  4. `mycobot280pi_gui/grcn_pyqt_widget.py`(A custom PyQt widget for the image display)

---

### `planner_robot_node` Node Breakdown 🤖

- **Predicted Complexity:** Very Long

- **Possible Dependencies:** `rclpy`, `mycobot280pi_interfaces`, `sensor_msgs`

- **Separation of Concerns:**
  
  1. `mycobot280pi_planner/rpn_main_ros_node.py`(The main ROS node file)
  
  2. `mycobot280pi_planner/rpn_planning_logic.py`(The core Finite-State-Machine implementation for planning and decision-making logic)
  
  3. `mycobot280pi_planner/rpn_action_server.py`(A class to handle the action server)
  
  4. `mycobot280pi_planner/rpn_service_server.py`(A class to handle the service server)

---

### `robot_mycobot_joint_publisher_node` Node Breakdown 🦾

- **Predicted Complexity:** Short

- **Possible Dependencies:** `rclpy`, `pymycobot`, `sensor_msgs/msg/JointState`

- **Separation of Concerns:**
  
  - `mycobot280pi_robot/mjpn_main_ros_node.py` (The main ROS node file that performs a simple API read and publishes a single topic)

---

### `robot_mycobot_executor_node` Node Breakdown 🏃

- **Predicted Complexity:** Long

- **Possible Dependencies:** `rclpy`, `mycobot280pi_interfaces`, `pymycobot`

- **Separation of Concerns:**
  
  1. `mycobot280pi_robot/rmen_main_ros_node.py`(The main ROS node file)
  
  2. `mycobot280pi_robot/rmen_mycobot_interface.py`(A module that encapsulates the pymycobot API calls)
  
  3. `mycobot280pi_robot/rmen_robot_state_manager.py`(A module for handling the robot's current FSM state and errors)

---

# ===== PACKAGE DEPENDENCIES =======

[last edit: 6 Sep 2025 17:29]

### 1. `mycobot280pi_interfaces` Package Dependencies 📦

This package contains no nodes. It holds the custom message, service, and action definitions that all the other packages will use for communication.

From `src` directory:

#### Package Creation + Dependencies Flag

```bash
ros2 pkg create mycobot280pi_interfaces --build-type ament_cmake --dependencies std_msgs action_msgs
```

##### Standard ROS 2 Interfaces Dependencies

- `std_msgs`:  builtin interface
  
  - **`std_msgs/Header`**: for`ManyDetectedObjects.msg` timestamps and frame information.

- `action_msgs`: 
  
  - **`std_msgs/Header`** for `ProcessWorkspace.action` ROS 2 action system
  
  ---

### 2. `mycobot280pi_vision` Package Dependencies 🛠️ 📐 🎯

This package is for the entire vision pipeline. All nodes related to image capture, processing, and object detection belong here.

#### Package Creation + Dependencies Flag

From `src` directory:

```bash
ros2 pkg create mycobot280pi_vision --build-type ament_python --dependencies rclpy sensor_msgs mycobot280pi_interfaces cv_bridge
```

##### Core ROS 2 Dependencies

These are fundamental to any ROS 2 Python node.

1. `rclpy`: The core client library for Python.

##### Standard ROS2 Tools Dependencies

These are standard packages from the ROS 2 ecosystem for common data types and functionalities.

1. `cv_bridge` : The package to interface with OpenCV.  

##### Standard ROS2 Interfaces Dependencies

1. `sensor_msgs`: builtin interface
   
   - **`sensor_msgs/msg/Image`**: To subscribe to raw images from the camera  

##### Custom Interfaces Dependencies

1. `mycobot280pi_interfaces`: custom interface
   
   - **`mycobot280pi_interfaces/msg/Point2DArray`**: To receive perspective points from the GUI
   - **`mycobot280pi_interfaces/msg/ManyDetectedObjects`**: To publish the results of the object detection    

##### Third-Party Libraries Dependencies

This is an external library that provides the core algorithms for your vision nodes.

1. `OpenCV`: need to install this separately: `pip install opencv-contrib-python`

---

### 3. `mycobot280pi_robot` Package Dependencies 🦾📝🏃

This package contains the core robot control and state-reporting nodes that communicate directly with MyCobot 280 Pi or the ROS 2 ecosystem. It needs to be run on the MyCobot 280 Pi.

#### Package Creation + Dependencies Flag

From `src` directory:

```bash
ros2 pkg create mycobot280pi_robot --build-type ament_python --dependencies rclpy sensor_msgs tf2_ros tf2_msgs mycobot280pi_interfaces
```

##### Core ROS2 Dependencies

These are fundamental to any ROS 2 Python node.

1. `rclpy`: The core client library for Python.

##### Standard ROS2 Interfaces Dependencies

1. `sensor_msgs`: builtin interface
   
   - **`sensor_msgs/msg/JointState`**: To publish the robot's joint states for monitoring (`robot_mycobot_joint_publisher_node`).

2. `tf2_msgs`: builtin interface
   
   - **`tf2_msgs/msg/TFMessage`**: To broadcast the robot's state transforms (`mycobot_state_publisher_node`).

##### Custom Interfaces Dependencies

1. `mycobot280pi_interfaces`: custom interface
   
   - **`mycobot280pi_interfaces/msg/SimpleCommands`**: To receive commands from the planner and GUI (`robot_mycobot_executor_node`).

##### Third-Party Libraries Dependencies

1. `pymycobot`: The Python API used to interface with the MyCobot robot hardware.

---

### 4.`mycobot280pi_planner` Package Dependencies 🤖

This package holds the high-level logic for autonomous operation, including planning and command dispatch.

From `src` directory:

```bash
ros2 pkg create mycobot280pi_planner --build-type ament_python --dependencies rclpy mycobot280pi_interfaces sensor_msgs action_msgs
```

##### Core ROS2 Dependencies

These are fundamental to any ROS 2 Python node.

1. `rclpy`: The core client library for Python.

##### Custom Interfaces Dependencies

1. `mycobot280pi_interfaces`: custom interface
   
   - **`mycobot280pi_interfaces/msg/ManyDetectedObjects`**: To receive detected object data from the vision pipeline 
   - **`mycobot280pi_interfaces/msg/SimpleCommands`**: To send high-level commands to the robot executor node 
   - **`mycobot280pi_interfaces/srv/Mycobot280PiSetCoordsMadeSure`**: To receive requests for manual coordinate control from the GUI 
   - **`mycobot280pi_interfaces/action/ProcessWorkspace`**: To receive requests from the GUI to process the entire workspace

---

### 5.`mycobot280pi_gui` Package Dependencies 💻

This is the dedicated package for your user interface.

From `src` directory:

```bash
ros2 pkg create mycobot280pi_gui --build-type ament_python --dependencies rclpy mycobot280pi_interfaces sensor_msgs tf2_msgs
```

### Dependencies

These are the possible dependencies for this package, categorized and sorted.

##### Core ROS2 Dependencies

These are fundamental to any ROS 2 Python node.

1. `rclpy`: The core client library for Python.

##### Standard ROS2 Interfaces Dependencies

1. `sensor_msgs`: builtin interface
   
   - **`sensor_msgs/msg/Image`**: To display the different image streams, such as the undistorted and corrected images.
   - **`sensor_msgs/msg/JointState`**: To display the robot's current joint angles.

2. `tf2_msgs`: builtin interface
   
   - **`tf2_msgs/msg/TFMessage`**: To receive robot state data from the state broadcaster.

##### Custom Interfaces Dependencies

1. `mycobot280pi_interfaces`: custom interface
   
   - **`mycobot280pi_interfaces/msg/Point2DArray`**: To publish user-defined perspective points to the vision pipeline
   
   - **`mycobot280pi_interfaces/msg/ManyDetectedObjects`**: To display the final object detection results.
   
   - **`mycobot280pi_interfaces/msg/SimpleCommands`**: To send manual commands to the robot executor node
   
   - **`mycobot280pi_interfaces/srv/Mycobot280PiSetCoordsMadeSure`**: To send manual coordinate requests to the planner.
   
   - **`mycobot280pi_interfaces/action/ProcessWorkspace`**: To initiate an automated pick and place cycle.
     
     ##### Third-Party Libraries Dependencies

2. `PyQt5`: need to install this separately: `pip install PyQt5`

---

### 6. Standard ROS 2 Tool 📸 🖼️

It's pre-existent ROS2 packages. no need to make from scratch

---

# ====== EMPTY FILES AND FOLDER =====

### 1. `mycobot280pi_interfaces` Package Contents📦

This package contains no nodes. It holds the custom message, service, and action definitions that all the other packages will use for communication.

#### Interface Contents


#### Package Source File Creation

```bash
# Create necessary folders
mkdir -p mycobot280pi_interfaces/msg
mkdir -p mycobot280pi_interfaces/action
mkdir -p mycobot280pi_interfaces/srv
```

```bash
# Create .msg files
touch mycobot280pi_interfaces/msg/ManyDetectedObjects.msg
touch mycobot280pi_interfaces/msg/Mycobot280PiAngles.msg
touch mycobot280pi_interfaces/msg/Mycobot280PiCoords.msg
touch mycobot280pi_interfaces/msg/Mycobot280PiSetCoords.msg
touch mycobot280pi_interfaces/msg/OneDetectedObject.msg
touch mycobot280pi_interfaces/msg/Point2DArray.msg
touch mycobot280pi_interfaces/msg/Point2D.msg
touch mycobot280pi_interfaces/msg/SimpleCommands.msg
# Create .srv files
touch mycobot280pi_interfaces/srv/Mycobot280PiSetCoordsMadeSure.srv
# Create .action file
touch mycobot280pi_interfaces/action/ProcessWorkspace.action
```

### 2. `mycobot280pi_vision` Package Contents 🛠️📐🎯

#### Node Contents

##### `vision_undistorter_node` 🛠️

- **Separation of Concerns:**
  - `mycobot280pi_vision/vun_main_ros_node.py` (The main ROS node file).

##### `vision_perspective_transformer_node` 📐

- **Separation of Concerns:**
  - `mycobot280pi_vision/vptn_main_ros_node.py` (The main ROS node file).
  - `mycobot280pi_vision/vptn_perspective_transform.py` (The module with the core OpenCV transformation algorithm).

##### `vision_object_detector_node` 🎯

- **Separation of Concerns:**
  - `mycobot280pi_vision/vodn_main_ros_node.py` (The main ROS node file).
  - `mycobot280pi_vision/vodn_object_detection.py` (The module with the vision algorithm).
  - `mycobot280pi_vision/vodn_message_converter.py` (The module to convert data types to ROS messages).

#### Package Source File Creation

This bash script will create the necessary empty files for the `mycobot280pi_vision` package.

```bash
# This script should be run from the 'src' directory of your ROS 2 workspace

# Files for vision_undistorter_node (vun_)
touch mycobot280pi_vision/mycobot280pi_vision/vun_main_ros_node.py

# Files for vision_perspective_transformer_node (vptn_)
touch mycobot280pi_vision/mycobot280pi_vision/vptn_main_ros_node.py
touch mycobot280pi_vision/mycobot280pi_vision/vptn_perspective_transform.py

# Files for vision_object_detector_node (vodn_)
touch mycobot280pi_vision/mycobot280pi_vision/vodn_main_ros_node.py
touch mycobot280pi_vision/mycobot280pi_vision/vodn_object_detection.py
touch mycobot280pi_vision/mycobot280pi_vision/vodn_message_converter.py
```

---

### 3. `mycobot280pi_robot` Package Contents 🦾📝🏃


#### Node Contents

##### `robot_mycobot_joint_publisher_node` 🦾

- **Separation of Concerns:**
  - `mycobot280pi_robot/mjpn_main_ros_node.py` (The main ROS node file that performs a simple API read and publishes a single topic).

##### `robot_mycobot_executor_node` 🏃

- **Separation of Concerns:**
  - `mycobot280pi_robot/rmen_main_ros_node.py` (The main ROS node file).
  - `mycobot280pi_robot/rmen_mycobot_interface.py` (A module that encapsulates the pymycobot API calls).
  - `mycobot280pi_robot/rmen_robot_state_manager.py` (A module for handling the robot's current FSM state and errors).
  
#### Other Contents
URDF files that needs to be `xacro`-ed so it can be fed into `mycobot_state_publisher_node` 's `robot_description` parameter.


#### Package Source File Creation

This bash script will create the necessary empty files for the `mycobot280pi_robot` package.

```bash
# This script should be run from the 'src' directory of your ROS 2 workspace

# Folder for rviz2 robot description parameter
mkdir mycobot280pi_robot/mycobot280pi_robot/urdf

# Files for robot_mycobot_joint_publisher_node (rmjpn_)
touch mycobot280pi_robot/mycobot280pi_robot/rmjpn_main_ros_node.py

# Files for robot_mycobot_executor_node (rmen_)
touch mycobot280pi_robot/mycobot280pi_robot/rmen_main_ros_node.py
touch mycobot280pi_robot/mycobot280pi_robot/rmen_mycobot_interface.py
touch mycobot280pi_robot/mycobot280pi_robot/rmen_robot_state_manager.py
```

---

### 4. `mycobot280pi_planner` Package Contents 🤖

#### Node Contents

##### `planner_robot_node` 🤖

- **Separation of Concerns:**
  - `mycobot280pi_planner/rpn_main_ros_node.py` (The main ROS node file).
  - `mycobot280pi_planner/rpn_planning_logic.py` (The core Finite-State-Machine implementation for planning and decision-making logic).
  - `mycobot280pi_planner/rpn_action_server.py` (A class to handle the action server).
  - `mycobot280pi_planner/rpn_service_server.py` (A class to handle the service server).

#### Package Source File Creation

This bash script will create the necessary empty files for the `mycobot280pi_planner` package.

```bash
# This script should be run from the 'src' directory of your ROS 2 workspace

# Files for planner_robot_node (rpn_)
touch mycobot280pi_planner/mycobot280pi_planner/rpn_main_ros_node.py
touch mycobot280pi_planner/mycobot280pi_planner/rpn_planning_logic.py
touch mycobot280pi_planner/mycobot280pi_planner/rpn_action_server.py
touch mycobot280pi_planner/mycobot280pi_planner/rpn_service_server.py
```

---

### 5. `mycobot280pi_gui` Package Contents 💻

#### Node Contents

##### `gui_robot_control_node` 💻

- **Separation of Concerns:**
  - `mycobot280pi_gui/grcn_main.py` (The main entry point).
  - `mycobot280pi_gui/grcn_pyqt_gui_app.py` (The main GUI window and layout with PyQt).
  - `mycobot280pi_gui/grcn_ros_communication.py` (The ROS communication class).
  - `mycobot280pi_gui/grcn_pyqt_widget.py` (A custom PyQt widget for the image display).

#### Package Source File Creation

This bash script will create the necessary empty files for the `mycobot280pi_gui` package.

```bash
# This script should be run from the 'src' directory of your ROS 2 workspace

# Files for gui_robot_control_node (grcn_)
touch mycobot280pi_gui/mycobot280pi_gui/grcn_ain.py
touch mycobot280pi_gui/mycobot280pi_gui/grcn_qt_gui_app.py
touch mycobot280pi_gui/mycobot280pi_gui/grcn_communication.py
touch mycobot280pi_gui/mycobot280pi_gui/grcn_widget.py
```

---

### 6. Standard ROS 2 Tool 📸 🖼️

It's pre-existen ROS2 packages. no need to build anything

---

# ====== IMPORTANT FILES AND FOLDERS =====

```bash
.
└── src
    ├── mycobot280pi_interfaces
    │   ├── msg
    │   │   ├── Mycobot280PiAngles.msg
    │   │   ├── Mycobot280PiCoords.msg
    │   │   ├── Mycobot280PiSetCoords.msg
    │   │   ├── OneDetectedObject.msg
    │   │   ├── ManyDetectedObjects.msg
    │   │   ├── Point2D.msg
    │   │   ├── Point2DArray.msg
    │   │   └── SimpleCommands.msg
    │   │       
    │   ├── srv
    │   │   ├── Mycobot280PiSetCoordsMadeSure.srv
    │   │   └── VacuumPumpV2SetPins.srv
    │   │    
    │   ├── action    
    │   │   └── ProcessWorkspace.action
    │   │
    │   ├── package.xml
    │   ├── CMakeLists.txt
    │   └── ...
    │ 
    ├── mycobot280pi_vision
    │   │    
    │   ├── mycobot280pi_vision
    │   │   ├── vodn_main_ros_node.py
    │   │   ├── vodn_message_converter.py
    │   │   ├── vodn_object_detection.py
    │   │   ├── vptn_main_ros_node.py
    │   │   ├── vptn_perspective_transform.py
    │   │   ├── vun_main_ros_node.py
    │   │   └── __init__.py
    │   │
    │   ├── package.xml
    │   ├── setup.py    
    │   └── ...
    │   
    ├── mycobot280pi_robot
    │   │
    │   ├── mycobot280pi_robot
    │   │   ├── mjpn_main_ros_node.py
    │   │   ├── msbn_main_ros_node.py
    │   │   ├── rmen_main_ros_node.py
    │   │   ├── rmen_mycobot_interface.py
    │   │   ├── rmen_robot_state_manager.py
    │   │   └── __init__.py
    │   │
    │   ├── package.xml
    │   ├── setup.py    
    │   └── ...
    │
    ├── mycobot280pi_planner
    │   │
    │   ├── mycobot280pi_planner
    │   │   ├── rpn_action_server.py
    │   │   ├── rpn_main_ros_node.py
    │   │   ├── rpn_planning_logic.py
    │   │   ├── rpn_service_server.py
    │   │   └── __init__.py
    │   │
    │   ├── package.xml
    │   ├── setup.py    
    │   └── ...
    │
    └── mycobot280pi_gui
        │
        ├── mycobot280pi_gui
        │   ├── grcn_main.py
        │   ├── grcn_pyqt_gui_app.py
        │   ├── grcn_pyqt_widget.py
        │   ├── grcn_communication.py
        │   └── __init__.py
        │
        ├── package.xml
        ├── setup.py
        └── ...
```

# LAUNCH FILES CREATION

we'r using 
