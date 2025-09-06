[LAST EDITED: 6 SEP 2025 15:32]

# Implementasi_MyCobot280pi_ROS2

branch `FINAL_VERSION`
this branch will be the one with clear patterns.    

--- 

# === HOW TO RUN THIS SYSTEM ===

### Starting the System

To get the system up and running, you will need to launch two separate launch files. One will handle the robot and planning, and the other will handle the user interface and vision.

#### 💻 Start the GUI and Vision Pipeline

Run this command from your **LAPTOP's** terminal to launch the user interface , planning, and the entire vision pipeline. This can be launched anywhere, even the robot itself.

```bash
ros2 launch mycobot280pi_gui start_gui_on_laptop.launch.py
```

#### 🤖 Start the Robot and Planner

Run this command from your **MyCobot 280 Pi 's'** terminal to launch the robot's hardware interface  node. THIS MUST BE ON THE MYCOBOT 280PI, because it communicates with pymycobot API.

```bash
ros2 launch mycobot280pi_robot start_robot_on_.py
```

---

# 📌 What to Code First (MVP Plan)

## ✅ Step 1: Set Up Basic Robot Communication

- Install ROS2 Galactic and test MyCobot’s movement.

- Write a simple ROS2 node to send movement commands.

- Verify LAN communication with the MyCobot 280 Pi.
  
  ## Step 2: Control the Vacuum Pump
  
  Write a script to turn the vacuum pump on/off via ROS2.
  Test picking up and releasing objects manually using commands.
  
  ## ✅ Step 3: Display Webcam Feed

- Use OpenCV to capture and display the video feed.

- Ensure real-time video streaming on your Qt5 GUI.
  
  ## Step 4: Basic Object Detection
  
  Detect a simple object using color or shape detection.
  Overlay the detected object's position on the webcam feed.
  
  ## Step 5: Move Robot to Object
  
  Convert detected object position into robot coordinates.

- Move the MyCobot to the object using simple hardcoded movements.
  
  ## Step 6: Automate Pick & Place
  
  Combine movement + vacuum pump control to complete one full cycle:
  Detect object.
  Move arm to object.
  Activate vacuum pump.
  Lift & move object to a fixed drop zone.
  Release object.

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

# ==== NODEs =======

### **1. `vision_usb_cam_node`** 📸

**"Ciri Khas":** The Raw Image Publisher
**Role:** Publisher
**Function:** Captures raw, barrel-distorted images from the webcam using the `usb_cam` package. It's the main image source for the pipeline.
**Expected Task:** Continuously stream raw images from the webcam.

### Communication

#### Publishers

1. `/camera/image_raw`
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_undistorter_node`.

---

### **2. `vision_undistorter_node`** 🛠️

**"Ciri Khas":** The Barrel Distortion Fixer
**Role:** Subscriber & Publisher
**Function:** Subscribes to `/camera/image_raw`, applies lens correction, and publishes a cleaner, undistorted image stream.
**Expected Task:** Provide undistorted images for downstream nodes.

### Communication

#### Subscribers

1. `/camera/image_raw`
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   
   * **Details:** Receives from `vision_usb_cam_node`.
     
     #### Publishers

2. `/vision/undistorted_image`
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_perspective_transformer_node` and `ui_robot_control_gui_node`.

---

### **3. `vision_perspective_transformer_node`** 📐

**"Ciri Khas":** The Perspective Aligner
**Role:** Subscriber & Publisher
**Function:** Listens for perspective points from the GUI and the latest undistorted image, performs a perspective transform, and publishes the corrected image.
**Expected Task:** Transform the image based on user-selected points and publish the result.

### Communication

#### Subscribers

1. `/vision/undistorted_image`
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_undistorter_node`.

2. `/vision/perspective_points`
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/Point2DArray`
   
   * **Details:** Receives from `ui_robot_control_gui_node`.
     
     #### Publishers

3. `/vision/corrected_image`
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_object_detector_node` and `ui_robot_control_gui_node`.

---

### **4. `vision_object_detector_node`** 🎯

**"Ciri Khas":** The Finder
**Role:** Subscriber & Publisher
**Function:** Subscribes to the perspective-corrected image, runs blob detection algorithm, and publishes detected object data and the image for the GUI.
**Expected Task:** Detect objects in the corrected image and publish results.

### Communication

#### Subscribers

1. `/vision/corrected_image`
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   
   * **Details:** Receives from `vision_perspective_transformer_node`.
     
     #### Publishers

2. `/vision/detected_objects`
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
   * **Details:** Publishes to `robot_planner_node` and `ui_robot_control_gui_node`.

---

### **5. `ui_robot_control_gui_node`** 💻

**"Ciri Khas":** The Commander
**Role:** User Interface
**Function:** The user interface for monitoring and controlling the robot. It displays live data, lets users set perspective points, displays the final detection results, provides manual controls, and initiates complex tasks.
**Expected Task:**

* Display image streams, final processed image, and object cutouts

* Allow interactive perspective editing

* Publish points to trigger a one-time scene processing

* Display the robot's current joint angles and Cartesian coordinates.

* Initiate robot planner and displays real time report
  
  ### Communication
  
  #### Subscribers
1. `/vision/undistorted_image`
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_undistorter_node`.

2. `/vision/corrected_image`
   
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_perspective_transformer_node`.

3. `/vision/detected_objects`
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
   * **Details:** Receives from `vision_object_detector_node`.

4. `/robot/joint_states`
   
   * **Interface Type:** `sensor_msgs/msg/JointState`
   * **Details:** Receives from `mycobot_joint_publisher_node`.

5. `tf`
   
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   
   * **Details:** Receives from `mycobot_state_broadcaster_node`.
     
     #### Publishers

6. `/vision/perspective_points`
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/Point2DArray`
   * **Details:** Publishes to `vision_perspective_transformer_node`.

7. `/robot/simple_commands`
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
   
   * **Details:** Publishes to `robot_mycobot_executor_node`.
     
     #### Service Clients

8. `/planner/set_coords`
   
   * **Interface Type:** `mycobot280pi_interfaces/srv/SetCoords`
   
   * **Details:** Sends requests to `robot_planner_node`.
     
     #### Action Clients

9. `/planner/process_workspace`
   
   * **Interface Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`
   * **Details:** Sends requests to `robot_planner_node`.

---

### **6. `robot_planner_node`** 🤖

**"Ciri Khas":** The Robot Planner
**Role:** Action Server, Service Server, Command Dispatcher
**Function:** Plan and execute a sequence of robot actions.
Allow both manual movement via service calls and automated planning via actions.
**Expected Task:** Plan and execute a sequence of robot actions and report progress back to the GUI.

### Communication

#### Subscribers

1. `/vision/detected_objects`
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
   
   * **Details:** Receives from `vision_object_detector_node`.
     
     #### Publishers

2. `/planner/commands`
   
   * **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
   
   * **Details:** Publishes to `robot_mycobot_executor_node`.
     
     #### Service Server

3. `/planner/set_coords`
   
   * **Interface Type:** `mycobot280pi_interfaces/srv/SetCoords`
   
   * **Details:** Receives requests from `ui_robot_control_gui_node`.
     
     #### Action Server

4. `/planner/process_workspace`
   
   * **Interface Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`
   * **Details:** Receives requests from `ui_robot_control_gui_node`.

---

### **7. `mycobot_joint_publisher_node`** 🦾

**"Ciri Khas":** The Robot Joint Reporter
**Role:** Publisher
**Function:** Publishes the robot’s joint states for visualization and monitoring.
**Expected Task:** Continuously report joint state.

### Communication

#### Publishers

1. `/robot/joint_states`
   * **Interface Type:** `sensor_msgs/msg/JointState`
   * **Details:** Publishes to `ui_robot_control_gui_node`.

---

### **8. `robot_mycobot_executor_node`** 🏃

**"Ciri Khas":** The Command Executor inside the actual robot
**Role:** MyCobot pymycobot API Executor
**Function:** Translates commands received from either the `robot_planner_node` or the  into physical actions for the MyCobot robot. This node directly controls the robot's motors and end-effector.
**Expected Task:** Perform robot actions as commanded.

### Communication

#### Subscribers

1. `/planner/commands`
   * **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
   * **Details:** Receives from `robot_planner_node`.
2. `/robot/simple_commands`
   * **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
   * **Details:** Receives from `ui_robot_control_gui_node`.

---

### **9. `ui_rviz2_node`** 🖼️

**"Ciri Khas":** The Extra Visualizer
**Role:** Visualization Tool
**Function:** Subscribes to a variety of topics to display a complete 3D visualization of the robot
**Expected Task:** Display robot and scene data for monitoring.

### Communication

#### Subscribers

1. `/robot/tf`
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** Receives from `mycobot_state_broadcaster_node`.

---

### **10. `mycobot_state_broadcaster_node`** 📝

**"Ciri Khas":** The State Broadcaster
**Role:** Publisher
**Function:** Publishes the robot’s internal state for visualization.
**Expected Task:** Broadcast robot state for RViz and other consumers.

### Communication

#### Publishers

1. `/robot/description`
   * **Interface Type:** `Parameter`
   * **Details:** Publishes a parameter for robot description.
2. `/robot/tf`
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** Publishes transforms.

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
           **Subscriber:** `vision_perspective_transformer_node`, 📐`ui_robot_control_gui_node`💻
2. **`/vision/corrected_image`**
           **Interface Type:** `sensor_msgs/msg/Image`
           **Publisher:** `vision_perspective_transformer_node`📐
           **Subscriber:** `vision_object_detector_node`🎯, `ui_robot_control_gui_node`💻
3. **`/vision/perspective_points`**
           **Interface Type:** `mycobot280pi_interfaces/msg/Point2DArray`
           **Publisher:** `ui_robot_control_gui_node`💻
           **Subscriber:** `vision_perspective_transformer_node`📐
4. **`/vision/detected_objects`**
           **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
           **Publisher:** `vision_object_detector_node`🎯
           **Subscriber:** `robot_planner_node`🤖, `ui_robot_control_gui_node`💻

---

### `/robot` Namespace

This namespace contains topics related to the physical robot's state and general commands.

1. **`/robot/simple_commands`**
           **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
           **Publisher:** `ui_robot_control_gui_node`💻
           **Subscriber:** `robot_mycobot_executor_node`🏃
2. **`/robot/joint_states`**
           **Interface Type:** `sensor_msgs/msg/JointState`
           **Publisher:** `mycobot_joint_publisher_node`📝
           **Subscriber:** `ui_robot_control_gui_node`💻
3. **`/robot/tf`**
           **Interface Type:** `tf2_msgs/msg/TFMessage`
           **Publisher:** `mycobot_state_broadcaster_node`📝
           **Subscriber:** `ui_rviz2_node`🖼️

---

### `/planner` Namespace

This namespace is used for all communication with the robot's planning node.

1. **`/planner/commands`** (Topic)
           **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
           **Publisher:** `robot_planner_node`🤖
           **Subscriber:** `robot_mycobot_executor_node`🏃
2. **`/planner/set_coords`** (Service)
           **Interface Type:** `mycobot280pi_interfaces/srv/SetCoords`
           **Client:** `ui_robot_control_gui_node`💻
           **Server:** `robot_planner_node``🤖
3. **`/planner/process_workspace`** (Action)
           **Interface Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`        
           **Client:** `ui_robot_control_gui_node`💻
           **Server:** `robot_planner_node`🤖

---

# ===== PACKAGEs =======

### **1. `mycobot280pi_interfaces`** 📦

 This package contains no nodes. It holds the custom message, service, and action definitions that all the other packages will use for communication.

--- 

### 2. `mycobot280pi_vision`  🛠️ 📐 🎯

This package is for the entire vision pipeline. All nodes related to image capture, processing, and object detection belong here.

1. **`vision_undistorter_node`** - The Barrel Distortion Fixer
2. **`vision_perspective_transformer_node`** - The Perspective Aligner
3. **`vision_object_detector_node`** - The Finder

---

### 3. `mycobot280pi_robot` 🦾📝🏃

This package contains the core robot control and state-reporting nodes that communicate directly with MyCobot 280 Pi or the ROS 2 ecosystem. It needs to be run on the MyCobot 280 Pi.

1. **`mycobot_joint_publisher_node`** - The Robot Joint Reporter
2. **`mycobot_state_broadcaster_node`** - The State Broadcaster
3. **`robot_mycobot_executor_node`** - The Command Executor

---

### 4.`mycobot280pi_planner` 🤖

This package holds the high-level logic for autonomous operation, including planning and command dispatch.

1. **`robot_planner_node`** - The Robot Planner

---

### 5.`mycobot280pi_gui` 💻

This is the dedicated package for your user interface.

1. **`ui_robot_control_gui_node`** - The Commander

---

### 6. Standard ROS 2 Tool 📸 🖼️

1. **`vision_usb_cam_node`** - The Raw Image Publisher from `usb_cam`
2. **`ui_rviz2_node`** - The Extra Visualizer from `rviz`

--- 

# ===== NODE DEPENDENCIES AND PARTS ======

[last edited 6 Sep 2025 15:22]

### `vision_undistorter_node` 🛠️

- **Predicted Complexity:** Short

- **Possible Dependencies:** `rclpy`, `sensor_msgs/msg/Image`, `cv_bridge`, `OpenCV`

- **Separation of Concerns:**
  
  - `mycobot280pi_vision/vun_main_ros_node.py` (The main ROS node file)

---

### `vision_perspective_transformer_node` 📐

- **Predicted Complexity:** Medium

- **Possible Dependencies:** `rclpy`, `sensor_msgs/msg/Image`, `mycobot280pi_interfaces/msg/Point2DArray`, `cv_bridge`, `OpenCV`

- **Separation of Concerns:**
  
  1. `mycobot280pi_vision/vptn_main_ros_node.py`(The main ROS node file)
  
  2. `mycobot280pi_vision/vptn_perspective_transform.py`(The module with the core OpenCV transformation algorithm)

---

### `vision_object_detector_node` 🎯

- **Predicted Complexity:** Long

- Possible Dependencies:** `rclpy`, `sensor_msgs/msg/Image`, `mycobot280pi_interfaces/msg/ManyDetectedObjects`, `cv_bridge`, `OpenCV`

- **Separation of Concerns:**
  
  1. `mycobot280pi_vision/vodn_main_ros_node.py`(The main ROS node file)
  
  2. `mycobot280pi_vision/vodn_object_detection.py`(The module with the vision algorithm)
  
  3. `mycobot280pi_vision/vodn_message_converter.py` (The module to convert data types to ROS messages)

---

### `ui_robot_control_gui_node` 💻

- **Predicted Complexity:** Very Long

- **Possible Dependencies:** `rclpy`, `mycobot280pi_interfaces`, `sensor_msgs`, `PyQt5`

- **Separation of Concerns:**
  
  1. `mycobot280pi_gui/urcgn_main.py`(The main entry point)
  
  2. `mycobot280pi_gui/urcgn_pyqt_gui_app.py` (The main GUI window and layout with PyQt)
  
  3. `mycobot280pi_gui/urcgn_ros_communication.py`(The ROS communication class)
  
  4. `mycobot280pi_gui/urcgn_pyqt_widget.py`(A custom PyQt widget for the image display)

---

### `robot_planner_node` 🤖

- **Predicted Complexity:** Very Long

- **Possible Dependencies:** `rclpy`, `mycobot280pi_interfaces`, `sensor_msgs`

- **Separation of Concerns:**
  
  1. `mycobot280pi_planner/rpn_main_ros_node.py`(The main ROS node file)
  
  2. `mycobot280pi_planner/rpn_planning_logic.py`(The core Finite-State-Machine implementation for planning and decision-making logic)
  
  3. `mycobot280pi_planner/rpn_action_server.py`(A class to handle the action server)
  
  4. `mycobot280pi_planner/rpn_service_server.py`(A class to handle the service server)

---

### `mycobot_joint_publisher_node` 🦾

- **Predicted Complexity:** Short

- **Possible Dependencies:** `rclpy`, `pymycobot`, `sensor_msgs/msg/JointState`

- **Separation of Concerns:**
  
  - `mycobot280pi_robot/mjpn_main_ros_node.py` (The main ROS node file that performs a simple API read and publishes a single topic)

---

### `mycobot_state_broadcaster_node` 📝

- **Predicted Complexity:** Short

- **Possible Dependencies:** `rclpy`, `tf2_msgs/msg/TFMessage`, `sensor_msgs/msg/JointState`

- **Separation of Concerns:**
  
  - `mycobot280pi_robot/msbn_main_ros_node.py`(The main ROS node file that reports the robot's FSM state)

---

### `robot_mycobot_executor_node` 🏃

- **Predicted Complexity:** Long

- **Possible Dependencies:** `rclpy`, `mycobot280pi_interfaces`, `pymycobot`

- **Separation of Concerns:**
  
  1. `mycobot280pi_robot/rmen_main_ros_node.py`(The main ROS node file)
  
  2. `mycobot280pi_robot/rmen_mycobot_interface.py`(A module that encapsulates the pymycobot API calls)
  
  3. `mycobot280pi_robot/rmen_robot_state_manager.py`(A module for handling the robot's current FSM state and errors)

---

# ===== PACKAGE DEPENDENCIES =======

### **1. `mycobot280pi_interfaces`** 📦

This package contains no nodes. It holds the custom message, service, and action definitions that all the other packages will use for communication.

From `src` directory:

#### Package Creation + Dependencies Flag

```bash
ros2 pkg create mycobot280pi_interfaces --build-type ament_cmake --dependencies std_msgs action_msgs
```

---

### 2. `mycobot280pi_vision` 🛠️ 📐 🎯

This package is for the entire vision pipeline. All nodes related to image capture, processing, and object detection belong here.

#### Package Creation + Dependencies Flag

From `src` directory:

```bash
ros2 pkg create mycobot280pi_vision --build-type ament_python --dependencies rclpy sensor_msgs mycobot280pi_interfaces cv_bridge
```

### Dependencies

These are the possible dependencies for this package, categorized and sorted.

##### Core ROS 2 Dependencies

These are fundamental to any ROS 2 Python node.

1. `rclpy`: The core client library for Python.

##### Standard ROS  Tools

These are standard packages from the ROS 2 ecosystem for common data types and functionalities.

1. `cv_bridge` : The package to interface with OpenCV.  

##### Standard ROS 2 Interfaces

1. `sensor_msgs`: builtin interface
   
   - **`sensor_msgs/msg/Image`**: To subscribe to raw images from the camera  

##### Custom Interfaces

1. `mycobot280pi_interfaces`: custom interface
   
   - **`mycobot280pi_interfaces/msg/Point2DArray`**: To receive perspective points from the GUI
   - **`mycobot280pi_interfaces/msg/ManyDetectedObjects`**: To publish the results of the object detection    

##### Third-Party Libraries

This is an external library that provides the core algorithms for your vision nodes.

1. `OpenCV`: need to install this separately: `pip install opencv-contrib-python`

---

### 3. `mycobot280pi_robot` 🦾📝🏃

This package contains the core robot control and state-reporting nodes that communicate directly with MyCobot 280 Pi or the ROS 2 ecosystem. It needs to be run on the MyCobot 280 Pi.

#### Package Creation + Dependencies Flag

From `src` directory:

```bash
ros2 pkg create mycobot280pi_robot --build-type ament_python --dependencies rclpy sensor_msgs tf2_ros tf2_msgs mycobot280pi_interfaces
```

### Dependencies

These are the possible dependencies for this package, categorized and sorted.

##### Core ROS 2 Dependencies

These are fundamental to any ROS 2 Python node.

1. `rclpy`: The core client library for Python.

##### Standard ROS 2 Interfaces

1. `sensor_msgs`: builtin interface
   
   - **`sensor_msgs/msg/JointState`**: To publish the robot's joint states for monitoring (`mycobot_joint_publisher_node`).

2. `tf2_msgs`: builtin interface
   
   - **`tf2_msgs/msg/TFMessage`**: To broadcast the robot's state transforms (`mycobot_state_broadcaster_node`).

##### Custom Interfaces

1. `mycobot280pi_interfaces`: custom interface
   
   - **`mycobot280pi_interfaces/msg/SimpleCommands`**: To receive commands from the planner and GUI (`robot_mycobot_executor_node`).

##### Third-Party Libraries

1. `pymycobot`: The Python API used to interface with the MyCobot robot hardware.

---

### 4.`mycobot280pi_planner` 🤖

This package holds the high-level logic for autonomous operation, including planning and command dispatch.

From `src` directory:

```bash
ros2 pkg create mycobot280pi_planner --build-type ament_python --dependencies rclpy mycobot280pi_interfaces sensor_msgs action_msgs
```

##### Core ROS 2 Dependencies

These are fundamental to any ROS 2 Python node.

1. `rclpy`: The core client library for Python.

##### Custom Interfaces

1. `mycobot280pi_interfaces`: custom interface
   
   - **`mycobot280pi_interfaces/msg/ManyDetectedObjects`**: To receive detected object data from the vision pipeline 
   - **`mycobot280pi_interfaces/msg/SimpleCommands`**: To send high-level commands to the robot executor node 
   - **`mycobot280pi_interfaces/srv/SetCoords`**: To receive requests for manual coordinate control from the GUI 
   - **`mycobot280pi_interfaces/action/ProcessWorkspace`**: To receive requests from the GUI to process the entire workspace

---

### 5.`mycobot280pi_gui` 💻

This is the dedicated package for your user interface.

From `src` directory:

```bash
ros2 pkg create mycobot280pi_gui --build-type ament_python --dependencies rclpy mycobot280pi_interfaces sensor_msgs tf2_msgs
```

### Dependencies

These are the possible dependencies for this package, categorized and sorted.

##### Core ROS 2 Dependencies

These are fundamental to any ROS 2 Python node.

1. `rclpy`: The core client library for Python.

##### Standard ROS 2 Interfaces

1. `sensor_msgs`: builtin interface
   
   - **`sensor_msgs/msg/Image`**: To display the different image streams, such as the undistorted and corrected images.
   - **`sensor_msgs/msg/JointState`**: To display the robot's current joint angles.

2. `tf2_msgs`: builtin interface
   
   - **`tf2_msgs/msg/TFMessage`**: To receive robot state data from the state broadcaster.

##### Custom Interfaces

1. `mycobot280pi_interfaces`: custom interface
   
   - **`mycobot280pi_interfaces/msg/Point2DArray`**: To publish user-defined perspective points to the vision pipeline
   - **`mycobot280pi_interfaces/msg/ManyDetectedObjects`**: To display the final object detection results.
   - **`mycobot280pi_interfaces/msg/SimpleCommands`**: To send manual commands to the robot executor node
   - **`mycobot280pi_interfaces/srv/SetCoords`**: To send manual coordinate requests to the planner.
   - **`mycobot280pi_interfaces/action/ProcessWorkspace`**: To initiate an automated pick and place cycle.
     
     ##### Third-Party Libraries

2. `PyQt5`: need to install this separately: `pip install PyQt5`

##### ---

### 6. Standard ROS 2 Tool 📸 🖼️
