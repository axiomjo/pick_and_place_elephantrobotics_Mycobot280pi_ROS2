### 3. `mycobot280pi_robot` Package Contents 🦾📝🏃

IMPORTANT! since \msg\simplecommands dont have feedback,
how will the planner know when to publish new step? or 
this package isnt done yaaaa.

to be added:
- individual joint control (mvp 1 style?)
- homing?
- getcoords?


#### Node Contents


##### `robot_mycobot_executor_node` 🏃

- **Separation of Concerns:**
  - `mycobot280pi_robot/rmen_main_ros_node.py` (The main ROS node file).
  this file is where we take care of all ros2 communication for this node.
  
  - `mycobot280pi_robot/rmen_mycobot_interface.py` (A module that encapsulates the pymycobot API calls).
  it does so by making an instance and making methods that wraps easch pymycobot api call.
  
  - `mycobot280pi_robot/rmen_robot_state_manager.py` (A module for handling the robot's current FSM state and errors). 
  it's a fsm manager? that manages the transitions.
  
  
##### `robot_mycobot_joint_publisher_node` 🦾

- **Separation of Concerns:**
  - `mycobot280pi_robot/rmjpn_main_ros_node.py` (The main ROS node file that performs a simple API read and publishes a single topic).

  
#### Other Contents
URDF files that needs to be `xacro`-ed so it can be fed into `mycobot_state_publisher_node` 's `robot_description` parameter.



