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



























