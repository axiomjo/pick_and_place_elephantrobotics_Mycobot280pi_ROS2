[LAST EDITED: 5 SEP 2025 16:21]

current final_version aim?  

### **1. vision_usb_cam_node** 📸
**"Ciri Khas":** The Raw Image Publisher

**Role:** Publisher

**Function:** Captures raw, barrel-distorted images from the webcam using the `usb_cam` package. It's the main image source for the pipeline.

**Expected Task:** Continuously stream raw images from the webcam.

**Communication:**
* **Publishers:** `/camera/image_raw` (`sensor_msgs/msg/Image`) to `vision_undistorter_node`

---

### **2. `vision_undistorter_node`** 🛠️
**"Ciri Khas":** The Barrel Distortion Fixer

**Role:** Subscriber & Publisher

**Function:** Subscribes to `/camera/image_raw`, applies lens correction, and publishes a cleaner, undistorted image stream.

**Expected Task:** Provide undistorted images for downstream nodes.

**Communication:**
* **Subscribers:** 
    *`/camera/image_raw` (`sensor_msgs/msg/Image`) from 'vision_usb_cam_node`  

* **Publishers:**
    * `/vision/undistorted_image` (`sensor_msgs/msg/Image`) to `vision_perspective_transformer_node` and `ui_robot_control_gui_node`  
    

---

### **3. `vision_perspective_transformer_node`** 📐
**"Ciri Khas":** The Perspective Aligner

**Role:** Subscriber & Publisher

**Function:** Listens for perspective points from the GUI and the latest undistorted image, performs a perspective transform, and publishes the corrected image.

**Expected Task:** Transform the image based on user-selected points and publish the result.

**Communication:**
* **Subscribers:**
    * `/vision/undistorted_image` (`sensor_msgs/msg/Image`) from `vision_undistorter_node`
    * `/vision/perspective_points` (`Custom Message`) from `ui_robot_control_gui_node`  
    
* **Publishers:**
    * `/vision/corrected_image` (`sensor_msgs/msg/Image`) to `vision_object_detector_node` and `ui_robot_control_gui_node`

---

### **4. `vision_object_detector_node`** 🎯
**"Ciri Khas":** The Finder

**Role:** Subscriber & Publisher

**Function:** Subscribes to the perspective-corrected image, runs blob detection algorithm, and publishes detected object data and the image for the GUI.

**Expected Task:** Detect objects in the corrected image and publish results.

**Communication:**
* **Subscribers:** 
     *`/vision/corrected_image` (`sensor_msgs/msg/Image`) from `vision_perspective_transformer_node`  

* **Publishers:** 
    * `/vision/detected_objects` (Custom Message) to `robot_planner_node` and `ui_robot_control_gui_node`

---

### **5. `ui_robot_control_gui_node`** 💻
**"Ciri Khas":** The Commander

**Role:** User Interface

**Function:** The user interface for monitoring and controlling the robot. It displays live data, lets users set perspective points, displays the final detection results,  provides manual controls, and initiates complex tasks.

**Expected Task:**
* Display image streams, final processed image, and object cutouts
* Allow interactive perspective editing
* Publish points to trigger a one-time scene processing
* Display the robot's current joint angles and Cartesian coordinates.  
* Initiate robot planner and displays real time report


**Communication:**
* **Subscribers:**
    * `/vision/undistorted_image` (`sensor_msgs/msg/Image`) from `vision_undistorter_node`
    * `/vision/corrected_image` (`sensor_msgs/msg/Image`) from `vision_perspective_transformer_node`
    * `/vision/detected_objects` (Custom Message) from `vision_object_detector_node`
    * `/joint_states` (`sensor_msgs/msg/JointState`) from `mycobot_joint_publisher_node`  
    
* **Publishers:**
     * `/vision/perspective_points` (`Custom Message`) to `vision_perspective_transformer_node`
     * `/robot/simple_commands` (`Custom Message`) to `robot_mycobot_executor_node`  

* **Service Clients:**
    * `/planner/set_coords` (`mycobot_interfaces/srv/SetCoords`) to `robot_serviceclient_translator_node`  

* **Action Clients:**
    * `/planner/process_workspace` (`Custom Action`) to `robot_planner_node`  
    
* **TF Listeners:**
    * `tf` (`tf2_msgs/msg/TFMessage`) from `mycobot_state_broadcaster_node`
---

### **6. `robot_planner_node`** 🤖
**"Ciri Khas":** The Robot Planner 

**Role:** Action Server, Service Server, Command Dispatcher

**Function:** Plan and execute a sequence of robot actions.

Allow both manual movement via service calls and automated planning via actions.

**Expected Task:** Plan and execute a sequence of robot actions and report progress back to the GUI.  

**Communication:**
* **Subscribers:**
    *`/vision/detected_objects` (`Custom Message`) from `vision_object_detector_node`
  
* **Publishers:**
    *`/planner/commands` (`std_msgs/msg/String`) to `robot_mycobot_executor_node`  

* **Service Server:** 
    * `/planner/set_coords` (`mycobot_interfaces/srv/SetCoords`) from `ui_robot_control_gui_node`

* **Action Server:**
    * `/planner/process_workspace` (`Custom Action`) from `ui_robot_control_gui_node


---

### **7. `mycobot_joint_publisher_node`** 🦾
**"Ciri Khas":** The Robot Joint Reporter

**Role:** Publisher

**Function:** Publishes the robot’s joint states for visualization and monitoring.

**Expected Task:** Continuously report joint state.

**Communication:**
* **Publishers:** 
   * `/robot/joint_states` (`sensor_msgs/msg/JointState`) to `mycobot_state_broadcaster_node` and `ui_robot_control_gui_node`


---

### **8. `robot_mycobot_executor_node`** 🏃
**"Ciri Khas":** The Command Executor inside the actual robot

**Role:** MyCobot pymycobot API Executor

**Function:** Translates commands received from either the `robot_planner_node` or the `robot_serviceclient_translator_node` into physical actions for the MyCobot robot. This node directly controls the robot's motors and end-effector.

**Expected Task:** Perform robot actions as commanded.

**Communication:**
* **Subscribers:** (various command topics)
   * `/planner/commands` (`std_msgs/msg/String`) from `robot_planner_node` and `robot_serviceclient_translator_node`
   * `/robot/simple_commands` (`Custom Message`) from `ui_robot_control_gui_node`

---

### **9. `ui_rviz2_node`** 🖼️
**"Ciri Khas":** The Extra Visualizer

**Role:** Visualization Tool

**Function:** Subscribes to a variety of topics to display a complete 3D visualization of the robot 

**Expected Task:** Display robot and scene data for monitoring.

**Communication:**

* **Subscribers:** 
   * `/robot/tf` (`tf2_msgs/msg/TFMessage`) from `mycobot_state_broadcaster_node`

---

### **10. `mycobot_state_broadcaster_node`** 📝
**"Ciri Khas":** The State Broadcaster

**Role:** Publisher

**Function:** Publishes the robot’s internal state for visualization.

**Expected Task:** Broadcast robot state for RViz and other consumers.

**Communication:**
* **Publishers:** 
   * `/robot/description` (parameter), 
   * `/robot/tf` (transforms)
---

this branch will be the one with clear patterns.

# 📌 What to Code First (MVP Plan)

## ✅ Step 1: Set Up Basic Robot Communication

- Install ROS2 Galactic and test MyCobot’s movement.

- Write a simple ROS2 node to send movement commands.

- Verify LAN communication with the MyCobot 280 Pi.
  

##  Step 2: Control the Vacuum Pump

Write a script to turn the vacuum pump on/off via ROS2.

Test picking up and releasing objects manually using commands.

## ✅ Step 3: Display Webcam Feed

- Use OpenCV to capture and display the video feed.
  
- Ensure real-time video streaming on your Qt5 GUI.
  

##  Step 4: Basic Object Detection

Detect a simple object using color or shape detection.

Overlay the detected object's position on the webcam feed.

##  Step 5: Move Robot to Object

Convert detected object position into robot coordinates.

- Move the MyCobot to the object using simple hardcoded movements.
  

##  Step 6: Automate Pick & Place

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

# Implementasi_MyCobot280pi_ROS2
haha. TA. 💀  
semoga repo yg ini branchingnya lebih rapih ya.

yg lawas ada di repo lama.
()[https://github.com/axiomjo/TA_jojo] 

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
| Deadline Countdown | Date Range          | Observation | Notes |
| :----------------- | :------------------ | :---------- | :---- |
| **S_SIDANG: -0** | Oct 13 - Oct 19     | *(SEMINAR AKTUAL Week)* | (Continue with seminar activities) |

| Deadline Countdown | Date Range          | Observation | Notes |
| :----------------- | :------------------ | :---------- | :---- |
| **BUKU_BAA: -17** | Oct 20 - Oct 26     |             |       |
| **BUKU_BAA: -10** | Oct 27 - Nov 02     |             |       |

***

## **MILESTONE: FINAL SUBMISSIONS (BUKU_BAA & SYAR_YUDI)**
### **Week of November 03 - November 09, 2025**

| Deadline Countdown | Date Range          | Observation | Notes                                          |
| :----------------- | :------------------ | :---------- | :--------------------------------------------- |
| **BUKU_BAA: -3** | Nov 03 - Nov 09     |             | **Deadline: BUKU BAA (Nov 7)**<br>**Deadline: SYARAT YUDIS (Nov 10)** |

***

## **MILESTONE: YUDISIUM!**
### **Week of November 10 - November 16, 2025**

| Deadline Countdown | Date Range          | Observation | Notes                           |
| :----------------- | :------------------ | :---------- | :------------------------------ |
| **YUDISIUM: -2** | Nov 10 - Nov 16     | *(YUDISIUM Week)* | **Event: YUDISIUM (Nov 12)** |

---

## Template for New Weeks (Non-Milestone)

Copy and paste this template for each new week, updating the countdown (`CODENAME: -XX`) and dates accordingly. Calculate the days remaining to the *next closest major deadline*.

| Deadline Countdown | Date Range          | Observation | Notes |
| :----------------- | :------------------ | :---------- | :---- |
| CODENAME: -XX      | YYYY-MM-DD - YYYY-MM-DD |             |       |

---

## Template for New Milestone Weeks

When you hit a week containing a deadline, use a banner like this, then a new table for that week's entry.

```markdown
***

## **MILESTONE: [YOUR MILESTONE CODENAME]**
### **Week of YYYY-MM-DD - YYYY-MM-DD**

| Deadline Countdown | Date Range          | Observation | Notes |
| :----------------- | :------------------ | :---------- | :---- |
| [CODENAME]: -[Days] | [Start Date] - [End Date] |             | **Deadline: [Date of Event]** |
