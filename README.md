[LAST EDITED: 3 SEP 2025 21:45]

current final_version aim?  

### **1. Camera Node** 📸
**"Ciri Khas":** The Raw Feeder

**Role:** Publisher

**Function:** Captures raw, barrel-distorted images from the webcam using the `usb_cam` package. It's the main image source for the pipeline.

**Expected Task:** Continuously stream raw images from the webcam.

**Communication:**
* **Publishers:** `/camera/image_raw` (`sensor_msgs/msg/Image`)

---

### **2. Raw Corrector Node** 🛠️
**"Ciri Khas":** The Barrel Fixer

**Role:** Subscriber & Publisher

**Function:** Subscribes to `/camera/image_raw`, applies lens correction, and publishes a cleaner, undistorted image stream.

**Expected Task:** Provide undistorted images for downstream nodes.

**Communication:**
* **Subscribers:** `/camera/image_raw` (`sensor_msgs/msg/Image`)
* **Publishers:** `/camera/image_undistorted` (`sensor_msgs/msg/Image`)

---

### **3. Perspective Correction Node** 📐
**"Ciri Khas":** The Work Area Adjuster

**Role:** Subscriber & Publisher

**Function:** Listens for perspective points from the GUI and the latest undistorted image, performs a perspective transform, and publishes the corrected image.

**Expected Task:** Transform the image based on user-selected points and publish the result.

**Communication:**
* **Subscribers:**
    * `/camera/image_undistorted` (`sensor_msgs/msg/Image`)
    * `/perspective/points` (Custom Message)
* **Publishers:**
    * `/corrected_image` (`sensor_msgs/msg/Image`)

---

### **4. Object Detection Node** 🎯
**"Ciri Khas":** The Finder

**Role:** Subscriber & Publisher

**Function:** Subscribes to the perspective-corrected image, runs your blob detection algorithm, and publishes detected object data and the image for the GUI.

**Expected Task:** Detect objects in the corrected image and publish results.

**Communication:**
* **Subscribers:** `/corrected_image` (`sensor_msgs/msg/Image`)
* **Publishers:** `/detected_objects` (Custom Message)

---

### **5. GUI Node** 💻
**"Ciri Khas":** The Commander

**Role:** Subscriber & Publisher

**Function:** The user interface for monitoring and controlling the robot. It displays images, lets users set perspective points, and displays the final detection results.

**Expected Task:**
* Display image streams and detection results
* Allow interactive perspective editing
* Publish points to trigger a one-time scene processing
* Display final processed image and object cutouts

**Communication:**
* **Subscribers:**
    * `/camera/image_undistorted` (`sensor_msgs/msg/Image`)
    * `/corrected_image` (`sensor_msgs/msg/Image`)
    * `/detected_objects` (Custom Message)
* **Publishers:**
    * `/perspective_points` (Custom Message)

---

### **6. SetCoords Service Server Node** 🤖
**"Ciri Khas":** The Robot Mover

**Role:** Service Server

**Function:** Receives coordinate requests (likely from a separate robot control node or GUI) and moves the robot accordingly.

**Expected Task:** Move robot and reply with success/failure.

**Communication:**
* **Service Server:** `/set_coords` (`mycobot_interfaces/srv/SetCoords`)

---

### **7. Joint State Publisher Node** 🦾
**"Ciri Khas":** The Joint Reporter

**Role:** Publisher

**Function:** Publishes the robot’s joint states for visualization and monitoring.

**Expected Task:** Continuously report joint positions.

**Communication:**
* **Publishers:** `/joint_states` (`sensor_msgs/msg/JointState`)

---

### **8. Executor Node** 🏃
**"Ciri Khas":** The Command Executor

**Role:** Subscriber & Executor

**Function:** Executes robot commands received from other nodes.

**Expected Task:** Perform robot actions as commanded.

**Communication:**
* **Subscribers:** (various command topics)

---

### **9. RViz Node** 🖼️
**"Ciri Khas":** The Visualizer

**Role:** Visualization Tool

**Function:** Visualizes robot state, camera feeds, and detected objects.

**Expected Task:** Display robot and scene data for monitoring.

**Communication:**
* **Subscribers:** (various topics as configured)

---

### **10. Robot State Publisher Node** 📝
**"Ciri Khas":** The State Broadcaster

**Role:** Publisher

**Function:** Publishes the robot’s URDF-based state for visualization and other nodes.

**Expected Task:** Broadcast robot state for RViz and other consumers.

**Communication:**
* **Publishers:** `/robot_description` (parameter), `/tf` (transforms)
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

## Weekly Logs (July - November 2025)

| Deadline Countdown | Date Range          | Observation                                | Notes                                                                   |
| :----------------- | :------------------ | :----------------------------------------- | :---------------------------------------------------------------------- |
| **P_DAFTAR: -50** | July 21 - July 27   | 💀 | 💀 |
| **P_DAFTAR: -43** | July 28 - Aug 03    | 💀 | 💀 |
| **P_DAFTAR: -36** | Aug 04 - Aug 10     | 💀 | 💀|
| **P_DAFTAR: -29** | Aug 11 - Aug 17     | 💀 | 💀 |
| **P_DAFTAR: -22** | Aug 18 - Aug 24     | 💀 | 💀|
| **P_DAFTAR: -15** | Aug 25 - Aug 31     | 💀 | 💀 |
| **P_DAFTAR: -8** | Sep 01 - Sep 07     |      💀                                      |                    💀                                                     |

***

## **MILESTONE: PRASEM REGISTRATION (P_DAFTAR)**
### **Week of September 08 - September 14, 2025**

| Deadline Countdown | Date Range          | Observation | Notes                         |
| :----------------- | :------------------ | :---------- | :---------------------------- |
| **P_DAFTAR: -1** | Sep 08 - Sep 14     |             | **Deadline: PRASEM DAFTAR (Sep 9)** |

***

## **MILESTONE: PRASEM (P_SIDANG)**
### **Week of September 15 - September 21, 2025**

| Deadline Countdown | Date Range          | Observation | Notes                          |
| :----------------- | :------------------ | :---------- | :----------------------------- |
| **P_SIDANG: -0** | Sep 15 - Sep 21     | *(PRASEM ACT Week)* | **Event: PRASEM ACTUAL (Starts Sep 15)** |

***

## **MILESTONE: DOSEN ESTETIKA & POSTER (D_ESTETIK)**
### **Week of September 22 - September 28, 2025**

| Deadline Countdown | Date Range          | Observation | Notes                           |
| :----------------- | :------------------ | :---------- | :------------------------------ |
| **D_ESTETIK: -10** | Sep 22 - Sep 28     |             | **Deadline: DOSEN ESTETIK (Sep 25)** |

| Deadline Countdown | Date Range          | Observation | Notes |
| :----------------- | :------------------ | :---------- | :---- |
| **S_DAFTAR: -7** | Sep 29 - Oct 05     |             |       |

***

## **MILESTONE: SEMINAR TA REGISTRATION (S_DAFTAR) & PRESENTATION (S_SIDANG)**
### **Week of October 06 - October 12, 2025**

| Deadline Countdown | Date Range          | Observation | Notes                                              |
| :----------------- | :------------------ | :---------- | :------------------------------------------------- |
| **S_DAFTAR: -0** | Oct 06 - Oct 12     | *(SEMINAR Week)* | **Deadline: SEMINAR DAFTAR (Oct 7)**<br>**Event: SEMINAR AKTUAL (Starts Oct 13)** |

***

## **MILESTONE: SEMINAR TA ACTUAL (CONTINUED)**
### **Week of October 13 - October 19, 2025**

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
