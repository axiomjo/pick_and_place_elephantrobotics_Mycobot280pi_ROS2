25 sept ini lagi bikin ulang.

# perkara interface package
barusan gw colcon build salah tempat.
trus ada colcon build bahwa cmake g bisa nemuin srv yg gw minta dia bikin. katanya gaada di current directory package gw. ternyata, beneran gw salah ngasih nama wkwkwkwkwk blom diupdate ke nama interface yg baru dan kedobelan extension .srv nya wkwkwkwkk lol.

habis dibenerin, colcon buildnya berhasil koq.

# lagi bikin vision_perspective_transformer_node 

# lagi ngedit gui node yg bagian camera sidebar n perspective editor

# lagi launchfiles. 
ternyata ada pola berulang buat nambahin custom files n folder di package ros. pake yg os.path.join, trus diganti nama directory nya.

# balik ke bikin gui.
asli ini bagian guwila gede pol,

ah kan gui punya ros node sendiri ya, itu masif bgt. jadi dia dibikinin thread dewean, supaya g ganggu pyqt gui. nah, itu dibikin di ros node class yg dipanggil sm ros communication.


## Why So Many Methods in _ROSnode class ? 🧑‍🍳

Think of the `_ROSNode` class as a **Head Chef** in a very advanced kitchen. This chef needs a separate recipe (a method) for every single task they perform. Your Head Chef is very capable and handles four different kinds of tasks:

1.  **Receiving Ingredients (Subscriptions):** The chef needs a specific procedure for what to do when a delivery arrives. For each of the **4** topics it subscribes to, it needs a unique callback method to handle that specific ingredient (e.g., raw images, joint angles).

      * *Result: 4 methods*

2.  **Sending Out Dishes (Publications):** The chef needs a recipe for preparing and sending out a dish. Your GUI asks it to publish points.

      * *Result: 1 method*

3.  **Handling Quick Orders (Services):** A service is like a quick, direct order: "Make me a coffee." There's a method to *take the order* (`call_simple_command_service`) and another method to *handle the confirmation* that the coffee was delivered (`_simple_command_done`).

      * *Result: 2 methods*

4.  **Managing Complex Catering Events (Actions):** An action is a long, multi-step task like catering a party. It requires a lot of back-and-forth communication.

      * A method to *accept the catering job* (`send_complex_action_goal`).
      * A method to handle the *initial confirmation* (`_goal_response`).
      * A method to give the customer *live updates* (`_action_feedback`).
      * A method to handle the *final result* (`_action_result`).
      * A method to *cancel the job* if needed (`cancel_action_goal`).
      * *Result: 5 methods*

Adding these up (4 + 1 + 2 + 5) gives you **12** distinct methods, each with a unique and necessary job for handling the complexities of ROS 2 communication.

# perkara object detection
kan annotated image aman yh.

teus ternyata many detected objects msg yg gw bikin, ga ngasih cutout ke GUI, 
trus sungguhan kudu balik bikin service baru 
aduh ini ngganti blueprint lagiiii

# perkara add draggable objects ke working plane
broooo itu sistem koordinatnya ancur lagi astagaaaaa
kudu ngedebug kyk waktu dulu gui 3 sept T-T

# perkara ngerefactor gui... lagi
yk, aku mumet sama pkg gui ku yg dulu krn ada beberapa file yg puuuuuuuanjang soro, trus gajelas mana ngimport mana, jadi direfactor lagi jadi gini. all this was once from grcn_*.py files. now its clearer! HAHA!

yg gila itu yg `grcn_gui_main_window.py` versi lawas, semuaan ditaro di sana. aku mo debug mumet sendiri.

`grcn_ros_communication.py` juga nggilani. action clientnya panjang.

untung bisa direfactor jadi gini hehehehe.

```

.
├── grcn_gui_main_entry.py
├── gui
│   ├── grcn_action_manager.py
│   ├── grcn_app_state.py
│   ├── grcn_main_window.py
│   ├── grcn_plane_manager.py
│   ├── grcn_selection_manager.py
│   ├── grcn_service_manager.py
│   ├── grcn_signal_connector.py
│   ├── __init__.py
│   ├── utils.py
│   └── widgets
│       ├── grcn_camera_panel.py
│       ├── grcn_control_panel.py
│       ├── grcn_dock_panel.py
│       ├── grcn_draggable_item.py
│       ├── grcn_perspective_editor.py
│       ├── grcn_point_handle.py
│       ├── grcn_working_plane.py
│       └── __init__.py
├── __init__.py
└── roscomm
    ├── grcn_ros_facade.py
    ├── grcn_ros_node.py
    ├── handlers
    │   ├── grcn_action_client_handler.py
    │   ├── grcn_service_client_handler.py
    │   ├── grcn_topic_subscriber_publisher_handler.py
    │   └── __init__.py
    └── __init__.py


            
```
# perkara service yg ga selengkap message dari simple command ke primitive command
AAAAHHHH BIKIN ULANG SAMBUNGAN DARI GUI KE PLANNER KE EXECUTOR. btw, 01 sampe 04 blom kuupdate astaga. ini bisa kelar sebelom besok tah? aku pingin selesai.

BODOAMAT INTINYA INTERFACE `simplecommands.msg`  sama `Mycobot280pisimplecommandsmadesure.srv` PADA GANTI. HAHAHAHA

```
# Interface type: mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure
# Filepath: src/mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure.srv
# Mycobot280PiSimpleCommandsMadeSure.srv

# Request
string command_type         # e.g. "move", "vacuum_on", "vacuum_off", "vacuum_weak", "set_rgb", "set_joint_angles", etc.

# For movement commands
float32[] coords           # [x, y, z, rx, ry, rz] for move commands (optional)
float32[] joint_angles     # For direct joint control (optional)
int32 speed                # Movement speed (optional)

# For RGB commands
int32 r                    # Red value (0-255)
int32 g                    # Green value (0-255)
int32 b                    # Blue value (0-255)

# for vacuum pump V2
uint8 vacuum_pin1_level   # (white wire) 
uint8 vacuum_pin2_level   # (yellow wire) HIGH/LOW

# For future extensibility, you can add:
string[] extra_strings     # For any extra string parameters
float32[] extra_floats     # For any extra float parameters
int32[] extra_ints         # For any extra int parameters
---
# Response
bool success
string message

```

```
# Interface type: mycobot280pi_interfaces/msg/SimpleCommands
# Filepath: src/mycobot280pi_interfaces/msg/SimpleCommands.msg
# SimpleCommands.msg
# A flexible message for atomic robot commands from planner to executor

string command_type         # e.g. "move", "vacuum_on", "vacuum_off", "vacuum_weak", "set_rgb", "set_joint_angles", etc.

# For movement commands
float32[] coords           # [x, y, z, rx, ry, rz] for move commands (optional)
float32[] joint_angles     # For direct joint control (optional)
int32 speed                # Movement speed (optional)

# For RGB commands
int32 r                    # Red value (0-255)
int32 g                    # Green value (0-255)
int32 b                    # Blue value (0-255)

# for vacuum pump V2
uint8 vacuum_pin1_level   # (white wire) 
uint8 vacuum_pin2_level   # (yellow wire) HIGH/LOW

# For future extensibility, you can add:
string[] extra_strings     # For any extra string parameters
float32[] extra_floats     # For any extra float parameters
int32[] extra_ints         # For any extra int parameters
```
# pada akhirnya, proyek ini kerasa useless krn cuma bisa dipake di robot ini n bentar lagi juga ditinggalin krn softwarenya obsolete. aku capek. tapi klo gaada proyek ini, aku bisa ga TA. it happens a lot in my uni life tbh. things exist, for my benefit, and none for others. im glad for it. and im sad for it. but i know He provides it all, just for me. it reminds me of my old thought. and it is a direct answer to it. i ... am loved and cared for :'D ! very very much!

# YK service serverku daritadi broken knp? lagi2 nyoba implementasiin sebuah fungsionalitas yg gaada di galactic
remind me buat kasih difference between ros distributions. mostly what doesnt exist ti galactic tapi ada di versi ros lain. bikin tabel or smth. agak ngeselin tbh

# yey publishenya waras
kan aku `ros2 topic echo /planner/msg_primitive_command`  
trus dapet deh echo-an topic tiap planner minta robotnya do smthg :D
```
command_type: set_rz_angle
coords:
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
joint_angles: []
speed: 0
r: 0
g: 0
b: 0
vacuum_pin1_level: 0
vacuum_pin2_level: 0
extra_strings: []
extra_floats: []
extra_ints: []
---
command_type: vacuum_strong
coords: []
joint_angles: []
speed: 0
r: 0
g: 0
b: 0
vacuum_pin1_level: 0
vacuum_pin2_level: 1
extra_strings: []
extra_floats: []
extra_ints: []
---
command_type: vacuum_strong
coords: []
joint_angles: []
speed: 0
r: 0
g: 0
b: 0
vacuum_pin1_level: 0
vacuum_pin2_level: 1
extra_strings: []
extra_floats: []
extra_ints: []
---
command_type: vacuum_strong
coords: []
joint_angles: []
speed: 0
r: 0
g: 0
b: 0
vacuum_pin1_level: 0
vacuum_pin2_level: 1
extra_strings: []
extra_floats: []
extra_ints: []
---


dst...

```
# OK EXECUTOR NODE UDH WARAS! MY WHOLE SYSTEM CAN RUN! tinggal nge-tweak kosmetics?

btw, **HOME_COORDS**  
>>> mc.send_angles([0,0,0,0,0,0],10)  
>>> mc.get_coords()  
[49.9, -64.3, 410.5, -90.26, -0.26, -89.73]  

**orientasi nunduk**
RX=180,  
RY= 0,   
rz = rotasi mboh  


**discrepancy send sama get?**
>>> mc.send_coords([186, 64, 40, 180, 0, -90],10)
>>> mc.get_coords()
[186.4, 63.3, 38.5, 179.96, -0.24, -89.99]

# btw, pymycobotnya beneran langsung jalanin hal laen klo ada yg dianggil wkwkwkwk
yea coz.. ITS NON BLOCKING WHAAAAAAAA keren bgt devsnya. asli.

# just in case, perlu manual control pymycobot lewat terminal
```
python3

>>> from pymycobot.mycobot import MyCobot
>>> from pymycobot import PI_PORT, PI_BAUD
>>> import RPi.GPIO
>>> mc = MyCobot(PI_PORT, PI_BAUD)

```

# AKU FRUSTASI SM INI ROBOT 
BERAPA SIH LIMITNYA???? MANA KLO GAMAU GABILANG, kan susah liatnya HWHWHQHWHQQHQHWXDSJNJDFSJKWQELSl 

capek, pingin bikin poster sama ppt sama buku T-T

ssh -Y er@169.254.0.1

source /opt/ros/galactic/setup.bash
source TA_JosephineD_2025/pick_and_place_elephantrobotics_Mycobot280pi_ROS2/install/setup.bash

source TA_JosephineD_2025/investigating_robot_ws/install/setup.bash

# udh nemu height yg ideal.

# lagi nambahin joint angles di gui


# BLEURGHHH WIDGETSKU GAK MASUK AKAL, refactor lagi. baru ntar nambahin.
```
widgets/
├── __init__.py
│
├── grcn_command_panel.py          # PANEL: Bottom action buttons
├── grcn_control_panel.py          # PANEL: Assembles right-side controls
├── grcn_monitor_panel.py          # PANEL: Assembles left-side monitors
└── grcn_workspace_panel.py        # PANEL: The main central 2D plane
│
├── components/
│   ├── __init__.py
│   │
│   ├── monitors/
│   │   ├── __init__.py
│   │   ├── grcn_annotated_camera_panel.py
│   │   ├── grcn_detected_objects_monitor.py
│   │   └── grcn_joint_monitor.py
│   │
│   ├── controls/
│   │   ├── __init__.py
│   │   ├── grcn_led_control.py
│   │   ├── grcn_rotation_control.py
│   │   └── grcn_vacuum_control.py
│   │
│   ├── editors/
│   │   ├── __init__.py
│   │   └── grcn_perspective_editor.py
│   │
│   └── graphics/
│       ├── __init__.py
│       ├── grcn_draggable_item.py
│       └── grcn_point_handle.py
```




# perkara executor yg kadang bisa kadang engga
OH TERNYATA KRN SATU ROBOT CUMA BOLEH SATU INSTANCE mc.
jadi... aku gbisa mecah fungsi itu jadi dua node...
jadiin satu di executor lol

# perkara camera usb yg portnya ga konsisten
v4l2-ctl --list-devices

# barusan, robot gw malfunctionnnnnn





# AKU BENCI NGETIK DI MYCOBOT ARGGHHHHHHHHHH
apaan coba? MASA GEDIT KADANG BIA KADANG GABIISA
KAN RESE


# aku gapaham .xacro .urdf itu apaan hiks















