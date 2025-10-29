
# kamis 23 okt
asli ini aneh bgt minggu ini dapet whole week ga keganggu, bisa buat TA.

Step in Old pick_and_place_object ,New HSM State Class,Purpose
"Steps 0, 1",,Initialize ,Already exists. Moves to Home/Ready.
Steps 2-6,ApproachPickPose,Move to the safe hover pose above the object.
Steps 7-8,GraspObject,Descend and activate the vacuum.
Steps 9-10,LiftToSafe,Lift the object to a safe travel height.
Steps 11-12,ApproachPlacePose,Move to the safe hover pose above the target.
Steps 13-14,ReleaseObject,Descend and deactivate the vacuum.
Step 15-16,ReturnToIdle,Lift to safe height and return to the main loop.


# rabu 22 okt 2025 HIERARCICHAL STATE MACHINES IN OOP! lets try thisssss
akhirnya aku bisa balik ke sini hahaha. ini mau bikin ulang alur complex command. mo pake paper yg dual arm fsm, dia pake hsm. gak fsm krn gak transisinya bakal kebanyakan dan prone to error, jadi langsung ke hsm aja. 

nah.. berearti, planner node gw... dirombak total WKWKWKWK soalnya bukan njalanin step by step lagi. berarti ini samaaja mbikin dari 0...? haha. ok.

ywd. baru sampe situ.

# selasa, 14 okt 2025 todo's


## observasi: my system is actually ok. tapi bagian primitive command nya gagal. jadi ndabisa pick n place, masih bisa dikontrol manual.

## balik2 halaman perlu nutak ngatik pose supaya ngadep samping... DAN butuh buku yg beneran bisa kebuka dan stay put wkwkwk, ngeselin bukunya.

## simpple commands jalan semua kok, yg engga itu yg planner hahaha.

## gaenak klo mo give smthg in relation to the workplace krn di working area gaada referensi objek2 yg kita liat di dunia nyata, so i will just overlay the cam feed to the bottom of the working area with alpha 10.

## planner node.. yeah  need to create a fsm buat planner node pas ngurusin gerak robot, klo nda, commandnya keperintah semua ke executor, aand it doesnt work. sadge.

## jadi... keknya... butuh ngembangin planner node

## dan, buat z, keknya lebih enak klo i sediain slider yg ada gravity di beberapa titik? kyk ubuntu loh.

## buat kerja, n dapet moneh, supaya bisa independen, 
i'll coba apply ke timedoor academy / kodingnext / . puingin dapet kurikulum mereka tbh. gaji... now thats hard. aku tau aku lebih lambat dari org2. aku gak secepet itu. aku juga ga se-powerful org yg bisa ngejuggle beberapa hal sekaligus. so, sampe bulan ini selesai, imma just kerjain TA. habisitu november cari kerja sampingan, kan praktikum juga udah selesai. trus desember buku n perintilan sidang udh selesai.

dari terminal laptop:
[planner_robot_node-6] [INFO] [1760406254.270523345] [planner_robot_node]: Waiting for EXECUTOR's command primitives action server: /planner/act_command_primitives...
[planner_robot_node-6] [INFO] [1760406254.272870553] [planner_robot_node]: Sending primitive goal: set_rgb
[planner_robot_node-6] [INFO] [1760406254.282880128] [planner_robot_node]: Primitive goal accepted. Waiting for result...
[planner_robot_node-6] [ERROR] [1760406254.472372233] [planner_robot_node]: Primitive command FAILED: set RGB to blue (ready/home). Message: 
[planner_robot_node-6] [INFO] [1760406254.475976357] [planner_robot_node]: Feedback: ERROR: set RGB to blue (ready/home) failed. 
[gui_robot_control_node-5] [INFO] [1760406254.491323596] [gui_robot_control_node]: Complex action finished. Success: False, Message: Pick and place failed for object 4. Detail: 

dari terminal mycobot:
 [INFO] [1760405926.443889010] [robot_executor_node]: EXECUTOR: move to array('f', [178.5, 169.5, 72.5, 180.0, 0.0, 0.0]) (asynchronous)
[robot_executor_node-1] [INFO] [1760405943.975933986] [robot_executor_node]: Received service request: move_joints
[robot_executor_node-1] [INFO] [1760405943.978555324] [robot_executor_node]: EXECUTOR: move joints to array('f', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
[robot_executor_node-1] [WARN] [1760405944.115736443] [robot_executor_node]: Failed getting joint states: object of type 'NoneType' has no len()
[robot_executor_node-1] [INFO] [1760405957.959450673] [robot_executor_node]: Received service request: move
[robot_executor_node-1] [INFO] [1760405957.963322147] [robot_executor_node]: EXECUTOR: move to array('f', [164.5, 164.5, 72.5, 180.0, 0.0, 0.0]) (asynchronous)
[robot_executor_node-1] [INFO] [1760405968.985270373] [robot_executor_node]: Received service request: move
[robot_executor_node-1] [INFO] [1760405968.987922434] [robot_executor_node]: EXECUTOR: move to array('f', [164.5, 164.5, 72.5, 180.0, 0.0, 100.4000015258789]) (asynchronous)
[robot_executor_node-1] [WARN] [1760405969.130458983] [robot_executor_node]: Failed getting joint states: object of type 'NoneType' has no len()
[robot_executor_node-1] [WARN] [1760405970.229440133] [robot_executor_node]: Failed getting joint states: object of type 'NoneType' has no len()
[robot_executor_node-1] [INFO] [1760405979.198682391] [robot_executor_node]: Received service request: move
[robot_executor_node-1] [INFO] [1760405979.204751162] [robot_executor_node]: EXECUTOR: move to array('f', [164.5, 164.5, 30.0, 180.0, 0.0, 100.4000015258789]) (asynchronous)
[robot_executor_node-1] [INFO] [1760406122.921178175] [robot_executor_node]: Received service request: move_joints
[robot_executor_node-1] [INFO] [1760406122.923784300] [robot_executor_node]: EXECUTOR: move joints to array('f', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
[robot_executor_node-1] [INFO] [1760406254.308660104] [robot_executor_node]: Received new action goal request: set_rgb. Accepting.
[robot_executor_node-1] [INFO] [1760406254.319829992] [robot_executor_node]: Executing action goal: set_rgb...
[robot_executor_node-1] [INFO] [1760406254.322464676] [robot_executor_node]: EXECUTOR: Set RGB (0, 0, 255)
[robot_executor_node-1] [INFO] [1760406254.486290996] [robot_executor_node]: Action SUCCEEDED: set_rgb
[robot_executor_node-1] [ERROR] [1760406254.491411700] [robot_executor_node]: Error raised in execute callback: Failed to update goal state: goal_handle attempted invalid transition from state SUCCEEDED with event SUCCEED, at /tmp/binarydeb/ros-galactic-rcl-action-3.1.3/src/rcl_action/goal_handle.c:95
[robot_executor_node-1] Traceback (most recent call last):
[robot_executor_node-1]   File "/opt/ros/galactic/lib/python3.8/site-packages/rclpy/action/server.py", line 324, in _execute_goal
[robot_executor_node-1]     execute_result = await await_or_execute(execute_callback, goal_handle)
[robot_executor_node-1]   File "/opt/ros/galactic/lib/python3.8/site-packages/rclpy/executors.py", line 107, in await_or_execute
[robot_executor_node-1]     return callback(*args)
[robot_executor_node-1]   File "/home/er/TA_JosephineD_2025/pick_and_place_elephantrobotics_Mycobot280pi_ROS2/install/mycobot280pi_robot/lib/python3.8/site-packages/mycobot280pi_robot/ren_action_server_command_primitive.py", line 82, in execute_primitive_command_callback
[robot_executor_node-1]     goal_handle.succeed()
[robot_executor_node-1]   File "/opt/ros/galactic/lib/python3.8/site-packages/rclpy/action/server.py", line 152, in succeed
[robot_executor_node-1]     self._update_state(_rclpy.GoalEvent.SUCCEED)
[robot_executor_node-1]   File "/opt/ros/galactic/lib/python3.8/site-packages/rclpy/action/server.py", line 116, in _update_state
[robot_executor_node-1]     self._goal_handle.update_goal_state(event)
[robot_executor_node-1] rclpy._rclpy_pybind11.RCLError: Failed to update goal state: goal_handle attempted invalid transition from state SUCCEEDED with event SUCCEED, at /tmp/binarydeb/ros-galactic-rcl-action-3.1.3/src/rcl_action/goal_handle.c:95
[robot_executor_node-1] [INFO] [1760406588.110642542] [robot_executor_node]: Received service request: move
[robot_executor_node-1] [INFO] [1760406588.113360709] [robot_executor_node]: EXECUTOR: move to array('f', [132.5, 95.5, 60.099998474121094, 180.0, 0.0, 0.0]) (asynchronous)

=====================
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




ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat /home/er/TA_JosephineD_2025/pick_and_place_elephantrobotics_Mycobot280pi_ROS2/src/mycobot280pi_urdf/urdf/mycobot_280_pi/mycobot280pi_with_pump_edited_to_match_mycobot280pi_urdf.urdf)"



# LAN nya for the first time ever, unavailable.
enp2s0          ethernet  unavailable   --            

trus kucoba pasang ke monitor kecil, ganyala blas.

# ASTAGA, TAU KNP? AKU KEBALIK MASANG POWER SAMA GND VACUUM PUMP NYA.
# PAS DICOPOT, robotnya WARAS WE, 



# BROOOO aku baru tau klo mycobot nyediain 
mc.sync_send_coords(coords,speed, mode, timeout=15) #YG BLOCKING, ternyata cuma yg non blocking dikasih while loop ;[
mc.send_coords(coords,speed,mode) # mode = 0 = ANGULAR mode, dia ngabil rute paling efisien gerak, makanya aneh. bisa jatoh2.  
mc.send_coords(coords,speed,mode) # mode = 1 = LINEAR mode. dia literally kyyk bikin garis lurus dari skrg ke posisi target.  
mc.get_error_information() # buat cek movenya error ga. aku sih dapet 32 klo tujuan send_coords gamasukakal  
mc.clear_error_information() #buat kosongin jadi 0 lagi. 

# BISA EDIT GO HOME BUTTON di GUI!
# EDIT PLANNER NODE BUAT PLANNING SEQUENCE PAKE yg sync!
# EDIT EXECUTOR NODE SUPAYA BISA NERIMA COMMAND_TYPE BARU INI!
# BIKIN KOMUNIKASI DARI EXECUTOR NODE KE GUI BUAT CEK COMMANDNYA ERROR GA SUPAYA ADA USER FEEDBACK (ini.... kyk complicated soro seh, tapi klo gaada ini, buwingung kok g jalan2.)


btw, aku nambahin alias di terimal mycobot WKWKWKWKWK

```
alias pymycobotterminal="python3 -i -c 'from pymycobot.mycobot import MyCobot; from pymycobot import PI_PORT, PI_BAUD; import RPi.GPIO; mc = MyCobot(PI_PORT, PI_BAUD)'"

alias rosonly='source /opt/ros/galactic/setup.bash'

alias bothrosandinstall='source /opt/ros/galactic/setup.bash && cd ~ && source TA_JosephineD_2025/pick_and_place_elephantrobotics_Mycobot280pi_ROS2/install/setup.bash

alias toworkspace='cd TA_JosephineD_2025/pick_and_place_elephantrobotics_Mycobot280pi_ROS2'
```



# ini habis nambahin launchfile di gui supaya bisa manual ngasih input X:=angka_berapa_si_/dev/videoX
ternyata launchfile gg juga, bisa nerima input


# yk, ku kembali ke desain ros awal yg ga kuambil krn susah tapi ternyata perlu wkwkwkwk

daripada gui ke planner buat simple commands,
mending langsung ke executioner wkwkwkwkwkw

jadi konsepnya rippling action. jadi klo user cancel action di gui, gui nerusin ke planner, trus planner cancel action ke executioner.


# aku frustasi "indentation error di robot_executor_node. line 162 mulu, gatau apaan, kuliat pake vscode juga gajelas, mboh mumet 
tapi klo gaada error itu, aku gabakal ngeh sama error2 lain sih. i think i neededd that.

# ini buku blom kelar. sy brain fog. lagi pingin nyelesain, tapi lagi lamban bgt jalan pikirannya rn. kyk setengah sadar. agak pusing sih. aku perlu nyelesain ini.
ok, bby jo. see u tmr i g.

# tau darimana arti error mappings? official docs wkwkwkwkwk aku aja yg gapaham pas dulu baca hahaha
https://docs.elephantrobotics.com/docs/mycobot_280_pi_en/3-FunctionsAndApplications/6.developmentGuide/python/2_API.html  

1.3 get_error_information()
function： Obtaining robot error information

Return value：

0: No error message.
1 ~ 6: The corresponding joint exceeds the limit position.
16 ~ 19: Collision protection.
32: Kinematics inverse solution has no solution.
33 ~ 34: Linear motion has no adjacent solution.

# im refactoring the gui, pake design pattern model view controller, supaya g spaghetti code lagi, dan aku actually bisa njelasin konsep besar package ini di bab 3. tapi waktuku cuma sehari. apa nutut?

jadi, proposed directory jadi gini

── mycobot280pi/              
    ├── __init__.py
    ├── grcn_entry_main.py
    ├── app_orchestrator_core.py
    │
    ├── core_layer/                # MODEL & CONTROLLER layer
    │   ├── __init__.py
    │   ├── state_enum_core.py
    │   ├── workspace_model_core.py
    │   └── controllers_core/
    │       ├── __init__.py
    │       ├── complex_cmd_hdlr_core.py  
    │       ├── simple_cmd_hdlr_core.py   
    │       └── workspace_ctrl_core.py
    │
    ├── gui_layer/                 # VIEW layer
    │   ├── __init__.py
    │   ├── main_window_gui.py
    │   ├── signal_connector_gui.py
    │   └── widgets_gui/
    │       ├── __init__.py
    │       ├── action_panel_gui.py
    │       ├── command_panel_gui.py
    │       ├── monitor_panel_gui.py
    │       ├── workspace_panel_gui.py
    │       └── graphics_gui/
    │           ├── __init__.py
    │           ├── draggable_item_gui.py
    │           └── point_handle_gui.py
    │
    └── ros_layer/                 # ROS2
        ├── __init__.py
        ├── ros_facade_bridge.py
        ├── ros_node_main.py
        └── handlers_ros/
            ├── __init__.py
            ├── action_client_hdlr.py
            ├── service_client_hdlr.py
            └── topic_hdlr.py


dan krn agak jelas class mana manggil class mana, 
Of course. This is the perfect time to map out the new relationships. A clear dependency map is like a blueprint for the refactoring process.

I've designed a format that shows both what a class **needs to be created** (its dependencies) and **who uses it** (its consumers). This should give you a very clear picture of how all the pieces will connect.

# penyakit koordinat GUI balik lagi. Aaaahhhhhhhh
knp ke-offset mulu sih? kapan warasnya?

# 13 oct, monday.
soooo, aku mundurin diri dari sidang periode ini. i just hope i can finish the book fast. because it starts to fly out of my brain, and i feel so disinterested in this book. im tired. and this is a second-second chance that i need, that i hope i didint need, but i need. im glad theres a second second chance.

and pak yudi, my supervisor showed me great mercy, and he didnt lash out on me for creating such a horrendous output. and im glad. 
so i'll chase it down. so im free, altho my sidang is actually on december. now how am i gonna tell my parents? i dont know. my mom will prolly be so tired. and so will the dosens. and i wanna crumple inside, and cry because even after receiving grace, im still this bad. and i got grace. grace it is.

im tired. i wish im fast and efficient and independent. but im not there yet. and im still growing, and my growth is so slow compared to other peeps. and i got grace. plenty of grace. the grace suffices. and one day, we'll get there jo. its ok. ur still deeply loved. i still love u ok. i got grace, so, you do too. now, lets use this grace that our dosen and mom gave well? and be a good jojo? ok?
