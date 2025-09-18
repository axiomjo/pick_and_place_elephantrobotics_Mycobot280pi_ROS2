[LAST EDITED: 18 SEP 2025 17:21]
this is my own thoughts abt my system. this is the core truth. its still long and gak rapih.

# Implementasi_MyCobot280pi_ROS2

branch `FINAL_VERSION`
this branch will be the one with clear patterns and naming conventions.    

# === SYSTEM OVERVIEW ===
![sketsa nodes](ASSET_README/ROS2_NODES_DESIGN.png)

Sistem robot + antarmuka visual untuk mempermudah pengoperasian Mycobot 280 pi, dalam menjalankan tugas vacuum-and-place.
Dilengkapi computer vision, sehingga bisa ngerti konteks objek di lingkungannya.

--- 

dibuat untuk Tugas Akhir  
Josephine Dermawan   
Institut Sains dan Teknologi Terpadu Surabaya  
2025  

yg berjudul :  
"Implementasi Lengan Robot MyCobot 280 Pi untuk Memindahkan Koleksi Tanaman Kering di antara Lembaran Buku"

# === Author's Note ===
Hi buat siapapun yg baca repo ini.  

tbh, aku gmw lanjutin proyek ini klo dah lulus. 
tapi semoga repo ini bisa jadi pintu masuk buat anak2 elektro (atau infor) di ISTTS
yg mo nyentuh ROS2 .

Selama development, aku pake:  
- Linux Ubuntu 20.04 *  
- ROS2 Galactic Geochelone *  
- pymycobot 3.4.7 **  
- OpenCV (opencv-contrib-python 4.12.0.88)  

* Linux sana ROS2 nya kudu sepasang, krn tiap distro ROS2 punya distro linux yg direkomendasiin. why? i dunno, its what their devs said. 
* aku kekeuh pake ini krn tahun 2025, elephantrobotics blom ngeluarin image buat upgrade rasppi robotnya, jadi stuck sama ubuntu 20.04 :[ . kyknya merek lebih pingin ngelanjutin mycobot yg jetson nano daripada pi. mboh ya.
** pymycobot ada versi terbaru, tapi krn aku gaberani ngutak-ngatik sistem robotnya, aku putusin laptopnya ngikut robotnya.
*** kampus punya lengan robot, ada 2. di jurusan teknik industri.

mungkin ini bakal jadi repo mati.  
tapi moga ada manfaatnya dikit lah.  

klo mau liat buku TA ku, bisa diakses di github repo yg ini (klo udh kubikin public LOL):
https://github.com/axiomjo/konten_TA# 

mulai dari sini ke bawah, bahasanya nyampur2 inggris indo ya. soalnya aku capek mikir.
jadi.... uhmmm... i'll choose whichever is easier for me anyways.
have fun exploring. u'll definitely find little notes here and there.

# === HOW TO RUN THIS SYSTEM ===


```
# TO-DO: LAUNCH FILE.

# SEMENTARA: NODE SATU-SATU.

 ros2 run mycobot280pi_gui gui_robot_control_node
 
 
v4l2-ctl --list-devices



ros2 run usb_cam usb_cam_node_exe --ros-args --remap /image_raw:=/camera/image_raw -p camera_info_url:="file:///home/axiomjo/lab_robotik/eksperimental/ws_ROS2_mycobot280pi/src/CAM_object_detect/my_camera_capture/hardware_specifics/camera_calibration.yaml" -p camera_name:="my_camera" -p video_device:="/dev/video3"

ros2 run mycobot280pi_vision vision_undistorter_node --ros-args -p camera_info_file:="/home/axiomjo/lab_robotik/eksperimental/ws_ROS2_mycobot280pi/src/CAM_object_detect/my_camera_capture/hardware_specifics/camera_calibration.yaml"


ros2 run mycobot280pi_vision vision_perspective_transform_node

ros2 run mycobot280pi_vision vision_object_detector_node





ros2 run mycobot280pi_planner planner_robot_node

ros2 run mycobot280pi_robot robot_mycobot_joint_publisher_node

```

---

[PENAMAAN INI UDH FIX, GA GANTI2 LAGI.]
# ==== NODE COMMUNICATION =======

### **1. `vision_usb_cam_node`** Node 📸  (ROS2 PRE-BUILT PKG)

**"Ciri Khas":** The Streamer.  
**Function:** Captures raw, barrel-distorted images from the webcam using the ROS2's preexisting `usb_cam` package. It's the main image source for the pipeline. serius ini gunanya cuma ngasih image stream aja wkwkwkwkwk.  
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
#### Node Communication Role

##### Publishers

1. `/camera/msg_image_raw` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_undistorter_node`.

---

### **2. `vision_undistorter_node`**  Node 🛠️

**"Ciri Khas":** The Barrel Distortion Fixer  
**Function:** Subscribes to the topic `/camera/image_raw`, applies lens correction, and publishes a cleaner, undistorted image stream. btw, dapet data buat ngoreksi distortionnya pake ChArUCo 10x10. trus aku pake python script buat generate .yaml file untuk nyimpen data-data cameranya.  
**Expected Task:** Provide undistorted images for downstream nodes.  

#### Node Parameter Configuration

1. `camera_info_url` Parameter
   * **Interface Type:** `String`
   * **Details:** This parameter should be filled with the absolute path to a YAML file containing the camera's intrinsic calibration data from `camera_calibration.yaml`, which was generated from running the python script `charuco_calibration_file.py` inside `hardware_specifics`directory inside the vision package.  This file is used by the node to correct lens distortion in the image stream.

```
   INI NTAR FILEPATHNYA KUDU DIURUS SM LAUNCHFILES. use FindPackageShare in the Python launch file. SO IT CAN dynamically finds the path to the package at runtime. tapi sementara, absolute dulu y.
   
   --ros-args -p camera_info_file:="/home/axiomjo/lab_robotik/eksperimental/ws_ROS2_mycobot280pi/src/CAM_object_detect/my_camera_capture/hardware_specifics/camera_calibration.yaml"
   
```

#### Node Communication Role

##### Subscribers

1. `/camera/msg_image_raw` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_usb_cam_node`.
     
##### Publishers

1. `/vision/msg_undistorted_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_perspective_transformer_node` and `gui_robot_control_node`.

---

### **3. `vision_perspective_transformer_node`** Node 📐

**"Ciri Khas":** The Alligner  
**Function:** Subscribes to image stream`/vision/msg_undistorted_image` from the node before, and also subscribes to `/vision/msg_four_perspective_points` that was provided by the GUI.it then performs a perspective transform, and publishes the corrected image at the topic `/vision/msg_top_down_image` . yk, kyk fitur cam scanner yg geser2 titik buat nge-crop dokumen, kyk fitur ibispaint X yg bisa perspective warp sebuah image :D. mereka inspirasiku wkwkwkwk.  
**Expected Task:** Transform the image based on user-selected points and publish the result.  

#### Node Communication Role

##### Subscribers

1. `/vision/msg_undistorted_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_undistorter_node`.

2. `/gui/msg_four_perspective_points` Topic
   * **Interface Type:** `mycobot280pi_interfaces/msg/Point2DArray`
   * **Details:** Receives from `gui_robot_control_node`.
     
##### Publishers

1. `/vision/msg_top_down_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `vision_object_detector_node` and `gui_robot_control_node`.

---

### **4. `vision_object_detector_node`** Node 🎯

**"Ciri Khas":** The Finder  
**Function:** constantly detects blob in the `/vision/msg_top_down_image` image stream from the node before, runs blob detection algorithm, gets their center points, draw bounding boxes, and publishes detected object data `/vision/msg_detected_objects`  and the image `/vision/msg_annotated_image`  for the GUI.  
**Expected Task:** Detect objects in the corrected image and publish results.  

#### Node Communication Role

##### Subscribers

1. `/vision/msg_top_down_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_perspective_transformer_node`.
     
##### Publishers

1. `/vision/msg_detected_objects` Topic
   * **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
   * **Details:** Publishes to `gui_robot_control_node`.

2. `/vision/msg_annotated_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Publishes to `gui_robot_control_node`.
  
---

### **5. `gui_robot_control_node`** Node 💻

**"Ciri Khas":** The Commander  
**Function:** take a deep breath... this one got a LOT of responsibilities as the gui. basically, it gives the user an easy way to control the visual correction, monitor the robot, and control the robot using simple and complex commands. and coz its so big, this node will be divided up into python modules.   

to control the visual correction, this node displays a smaller version of `/vision/msg_undistorted_image` and then overlaying that image with four draggable connected points. this gui node then publishes the mapped position of those points into an array in `/vision/msg_four_perspective_points`, so that `vision_perspective_transformer_node` can do its transformation. the resulting perspective transformed image`/vision/msg_top_down_image` is displayed in the gui. thus, users can keep adjusting the fours points until the whole 300mmx300mm workspace area is detected. 

btw, how does the system provide the objects that user can interact with in the workspace? well, the detected object information `/vision/msg_detected_objects` is used as the anchor to crop object images in the bounding box `/vision/msg_annotated_image` ! theen, through a series of geometric mathematical calculation to finally know where to put these cutouts in the user's workspace, u can see a simplified but correct-ish representation of the real world from top down view! fyi, from this project, i just learned that computer graphics coordinate system ISN'T EXACTLY THE SAME as a typical cartesian coordinate system... it's y axis is flipped... AND THE CENTER POINT of computer graphics coordinate system isn't in the center of the screen, its on the top left(?) corner of the screen. like, whyyyyyyy? i spent more than a day trying to give transforms so in the end it can mimic a conventional coordinate system :''''''''''''''''']  

then, to let the user tell the robot what things to move where A.K.A complex command, the gui have a workspace area where users can drag, drop, and edit the orientation of the detected image, before finally calling an action `/planner/act_complex_command` ! btw, this part stumped me coz thinking about a gui like this is NOT SMTHG i learned in any of my college classes :\ . i take inspiration from games hahahaha. this gui node then saves a list of "moved objects" and their "before-after" and shove it all to the `planner_robot_node`. good luck planner node, ur the one who has to think hard to complete this action hahahaha. along the progress that the planner node does, the gui will get feedback that will be displayed to the user. this way, u can know how much items left the robot needs to move around.  

to control the robot with simple commands, the gui provides buttons. A LOT OF BUTTONS. from a panel with a button to add a square, which can be used as a visual marker to move the robot to it's center point, and a button to tell the robot to go there, an EMERGENCY button to STOP AND GO TO HOME POSITION if anything bad happens, and even buttons to manually set the vacuum pump. the gui basically trriggers a service call for `/planner/srv_simple_command` so the  `planner_robot_node` can know when user wants to do simple stuff. btw, klo tadi habis nyuruh robotnya complex command, buttons ini semua, kecuali yg EMERGENCY, bakal ke-disable, kecuali kita rela cancel actionnya di tengah jalan...  

if the user want to refresh the scene since they felt that the current worksapce no longer reflect the real-world condition, they can always press the "refresh scene" button, and the gui's memory will be reset-ed into a fresh new clean slate, importing the objects that is detected in `/vision/msg_annotated_image`.   

btw, in the workspace, theres a small portion reserved for book fipping. user can flip the book pages and put items there to place stuff inside the book. honestly, i regret promising this feature in the proposal because it makes MY PROJECT HARDER THAN IT COULD'VE BEEN :c . but i guess it adds a cool memorable feature? idk. semoga ga sia2 mikir buat ini.  

lastly, to see the way this robot joints move in real-time, user can see the displayed `/robot/msg_joint_angles` that is presented in bars. i take inspiration from gazebo11's interface that lets user move the robot's end effector. fyi, mycobot has limits for their joints :[ klo kamu paksa dia muter lebih dari yg dia bisa... shell robotnya bisa retak... kan ga lucu ya... :c partnya bujubuneng mahalnya weh, jgn dah.  

**Rangkuman Tugas:**

* Display image streams & final processed image

* Allow interactive perspective editing

* Allow interactive workspace editing

* Reports the robot's current joint angles from J1 to J6 

* Initiate simple commands

* Initiate robot planner and displays real time report
  
#### Node Communication Role
  
##### Subscribers
1. `/vision/msg_undistorted_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_undistorter_node`.

2. `/vision/msg_detected_objects` Topic
   * **Interface Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
   * **Details:** Receives from `vision_object_detector_node`.

3. `/vision/msg_annotated_image` Topic
   * **Interface Type:** `sensor_msgs/msg/Image`
   * **Details:** Receives from `vision_object_detector_node`.

4. `/robot/msg_joint_angles` Topic
   * **Interface Type:** `sensor_msgs/msg/JointState`
   * **Details:** Receives from `mycobot_jointangles_publisher_node`.

   
##### Publishers

1. `/gui/msg_four_perspective_points` Topic
   * **Interface Type:** `mycobot280pi_interfaces/msg/Point2DArray`
   * **Details:** Publishes to `vision_perspective_transformer_node`.
 
    
##### Service Client

1. `/planner/srv_simple_command` Service
   * **Interface Type:** `mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure`
   * **Details:** Sends requests to `robot_planner_node`.
   
##### Action Clients

1. `/planner/act_complex_command` Action
   * **Interface Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`
   * **Details:** Sends requests to `robot_planner_node`.

---

### **6. `planner_robot_node`** Node 🤖

**"Ciri Khas":** The Robot Planner
**Function:** Plan and execute a sequence of robot actions. btw, node planner ini kan dapet 2 jenis perintah ya, yg complex sama yg simpel2. klo yg simpel,`/planner/srv_simple_command`, ya cuma dapet trus lakuin. klo yg complex, `/planner/act_complex_command`, ada feedback sepanjang lagi ngerjain. trus, gmn cara dia mikir? well, di dalem node ini, ada switch case yg panjang buat mecah perintah complex ke perintah primitif wkwkwkwkwkwk. trus si planner node ini bakal ngepublish `/planner/msg_primitive_commands` ke `mycobot_executor_node`. knp ga service? mumet. lebih gampang publish. dan mycobot bisa.

**Expected Task:** Plan and execute the generated sequence of robot commands. 

#### Node Communication Role
  
##### Publisher

1. `/planner/msg_primitive_command` Topic
   * **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
   * **Details:** Publishes to `mycobot_executor_node`.
     
##### Service Server

1. `/planner/srv_simple_command` Service
   * **Interface Type:** `mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure`
   * **Details:** Handles service requests from `gui_robot_control_node`.
   
##### Action Server

1. `/planner/act_complex_command` Action
   * **Interface Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`
   * **Details:** Handles action requests and give feedback to `gui_robot_control_node`.

---

### **7. `mycobot_executor_node`** Node🏃

**"Ciri Khas":** The Command Executor inside the actual robot
**Role:** MyCobot pymycobot API Executor
**Function:** Translates commands to ElephantRobotics'  pymycobot API calls in the robot.
**Expected Task:** Perform robot actions as commanded.

#### Node Communication Role

##### Subscribers

1. `/planner/msg_primitive_command` Topic
   * **Interface Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
   * **Details:** Receives from `planner_robot_node`.

---

### **8. `mycobot_jointangles_publisher_node`** Node 🦾

**"Ciri Khas":** The Robot Joint Reporter
**Role:** Publisher
**Function:** calls the getangles() pymycobot API and publishes the each joint angles to `/robot/msg_joint_angles` for GUI visualization and monitoring.
**Expected Task:** Continuously report joint state.

#### Node Communication Role

##### Publishers

1. `/robot/msg_joint_angles` Topic
   * **Interface Type:** `sensor_msgs/msg/JointState`
   * **Details:** Publishes to `gui_robot_control_node`.

---

### **9. `mycobot_state_publisher_node`** Node 📝 (ROS2 PRE-BUILT PKG)

**"Ciri Khas":** The State Broadcaster
**Role:** Publisher
**Function:** Publishes the robot’s internal state for rviz2 visualization using ROS2's preexisting  `robot_state_publisher` package.
**Expected Task: Broadcast robot state for rviz2.

#### Node Parameter Configuration
1. `robot_description` Parameter
   * **Interface Type:** `String`
   * **Details:** This parameter should be filled with  MyCobot290Pi robot's entire model in the Unified Robot Description Format (URDF). This is an example of it in my machine
   
```
I NEED MY LAUNCH FILE TO IMPORT XACRO AND PROCESS IT INSIDE AND THENNN PASS IT AS A LAUNCH FILE PARAM. ya tapi krn aku blom launch files, jadi di terminal gini dulu y.

   XACROED=$(xacro "/home/axiomjo/lab_robotik/eksperimental/ws_ROS2_mycobot280pi/install/mycobot_description/share/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi_with_pump.urdf" )

ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="${XACROED}"
```
#### Node Communication Role

##### Publishers

1. `/rviz2/tf_static` Topic
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** Publishes the static transforms for the robot. These are the fixed relationships between a robot's links and are defined by the URDF.  Publishes to `ui_rviz2_node`.
   
2. `/rviz2/tf` Topic
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** This topic publishes the dynamic transforms of the robot, which are the transforms that change based on the joint states. Publishes to `ui_rviz2_node`.

 
---



### **10. `ui_rviz2_node`** Node 🖼️ (ROS2 PRE-BUILT PKG)

**"Ciri Khas":** The Extra Visualizer
**Role:** Visualization Tool
**Function:** Subscribes to a variety of topics to display a complete 3D visualization of the robot using the ROS2's preexisting `rviz2` package
**Expected Task:** Display robot and scene data for monitoring.

#### Node Communication Role

##### Subscribers

1. `/rviz2/tf_static` Topic
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** Receives the static transforms for the robot. These are the fixed relationships between a robot's links and are defined by the URDF. Receives from `mycobot_state_publisher_node`. 
     
2. `/rviz2/tf` Topic
   * **Interface Type:** `tf2_msgs/msg/TFMessage`
   * **Details:** Receives from `mycobot_state_publisher_node`.



---


