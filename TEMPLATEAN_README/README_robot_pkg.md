
# `mycobot280pi_interfaces` Package Breakdown

[Only from README.md , blom detail]

if i only look at the README.md , this is what exists:
```
mycobot280pi_interfaces/
├── action/
│   └── ProcessWorkspace.action
├── msg/
│   ├── Point2DArray.msg
│   ├── ManyDetectedObjects.msg
│   ├── SimpleCommands.msg
│   │
│   ├── OneDetectedObject.msg
│   └── Point2D.msg
├ 
├── srv/
│   └── Mycobot280PiSetCoordsMadeSure.srv
├── CMakeLists.txt
└── package.xml


```

```
touch msg/Point2DArray.msg
touch msg/ManyDetectedObjects.msg
touch msg/SimpleCommands.msg

touch srv/Mycobot280PiSetCoordsMadeSure.srv

touch action/ProcessWorkspace.action





touch mycobot280pi_interfaces/msg/Point2D.msg
touch mycobot280pi_interfaces/msg/OneDetectedObject.msg
```


but this feels insufficient, bcoz the interfaces i can collect from reusing old packages are:
```
mycobot280pi_interfaces/
    │   ├── msg/
    │   │   ├── Mycobot280PiAngles.msg
    │   │   ├── Mycobot280PiCoords.msg
    │   │   ├── Mycobot280PiSetCoords.msg
    │   │   ├── OneDetectedObject.msg
    │   │   ├── ManyDetectedObjects.msg
    │   │   ├── Point2D.msg
    │   │   ├── Point2DArray.msg
    │   │   └── SimpleCommands.msg
    │   │       
    │   ├── srv/
    │   │   ├── Mycobot280PiSetCoordsMadeSure.srv
    │   │   └── VacuumPumpV2SetPins.srv
    │   │    
    │   ├── action/  
    │   │   └── ProcessWorkspace.action
    │   │
    │   ├── package.xml
    │   ├── CMakeLists.txt
    │   └── ...

```

THUS, I NEED TO UPDATE the MAIN README.md , OR just scrap those.
### "To Be Added" to the `README.md`

---

#### Missing Interfaces from this project

  * **Message (`.msg`) Files:**

      * `Mycobot280PiAngles.msg`
      * `Mycobot280PiCoords.msg`
      * `Mycobot280PiSetCoords.msg`
      * `OneDetectedObject.msg`

  * **Service (`.srv`) Files:**

      * `VacuumPumpV2SetPins.srv`

#### Corresponding `touch` Commands

These commands create the files for the missing interfaces.

```bash
# Missing .msg files
touch mycobot280pi_interfaces/msg/Mycobot280PiAngles.msg
touch mycobot280pi_interfaces/msg/Mycobot280PiCoords.msg
touch mycobot280pi_interfaces/msg/Mycobot280PiSetCoords.msg



# Missing .srv files
touch mycobot280pi_interfaces/srv/VacuumPumpV2SetPins.srv
```
---
## PACKAGE DESCRIPTION:

**Role**: This package is an interface definition package. It contains no executable code or nodes. Its sole purpose is to define the custom messages, services, and actions used by the other packages in the `mycobot280pi_interfaces` workspace. This allows all nodes to communicate using a common, consistent set of data types.

## Currently Existing Topics, Services, Actions

### `ManyDetectedObjects.msg`

* **Used by:** `vision_object_detector_node` (publishes) and `planner_robot_node`, `gui_robot_control_node` (subscribes).
* **Description:** This compount interface message is used to publish the data for all objects detected by the vision pipeline.

### `OneDetectedObject.msg`

* **Used by:** `vision_object_detector_node` (publishes) and `planner_robot_node`, `gui_robot_control_node` (subscribes).
* **Description:** This message is used to hold data for an objects detected by the vision pipeline.

### `Point2DArray.msg`

* **Used by:** `gui_robot_control_node` (publishes) and `vision_perspective_transformer_node` (subscribes).
* **Description:** This compound interface message holds an array of 2D points, from `Point2DArray.msg`, representing the coordinates for the perspective transform.

### `Point2D.msg`

* **Used by:** `gui_robot_control_node` (publishes) and `vision_perspective_transformer_node` (subscribes).
* **Description:** This message holds one  2D points.



### `SimpleCommands.msg`

* **Used by:** `gui_robot_control_node` and `planner_robot_node` (publishers) and `planner_robot_node`, `robot_mycobot_executor_node` (subscribers).
* **Description:** This message is a simple command to execute, such as moving the robot or controlling the vacuum pump.

## Services

### `Mycobot280PiSetCoordsMadeSure.srv`

* **Used by:** `gui_robot_control_node` (client) and `planner_robot_node` (server).
* **Description:** This service is used to request the robot to move to a specific Cartesian coordinate. It is a remote procedure call that terminates after the action is completed.

## Actions

### `ProcessWorkspace.action`

* **Used by:** `gui_robot_control_node` (client) and `planner_robot_node` (server).
* **Description:** This action is used to initiate a complex, long-running task, such as an automated pick-and-place cycle. This action provides feedback to the client on the progress of the goal.




