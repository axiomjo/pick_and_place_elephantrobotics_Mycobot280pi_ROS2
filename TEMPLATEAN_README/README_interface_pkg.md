
# `mycobot280pi_interfaces` Package Breakdown

[Only from README.md , blom detail]

```
mycobot280pi_interfaces/
├── action/
│   └── ProcessWorkspace.action
├── msg/
│   ├── Point2DArray.msg
│   ├── ManyDetectedObjects.msg
│   └── SimpleCommands.msg
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
```

**Role**: This package is an interface definition package. It contains no executable code or nodes. Its sole purpose is to define the custom messages, services, and actions used by the other packages in the `mycobot280pi_interfaces` workspace. This allows all nodes to communicate using a common, consistent set of data types.

## Topics

### `ManyDetectedObjects.msg`

* **Used by:** `vision_object_detector_node` (publishes) and `planner_robot_node`, `gui_robot_control_node` (subscribes).
* **Description:** This message is used to publish the data for all objects detected by the vision pipeline.

### `Point2DArray.msg`

* **Used by:** `gui_robot_control_node` (publishes) and `vision_perspective_transformer_node` (subscribes).
* **Description:** This message holds an array of 2D points, representing the coordinates for the perspective transform.

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




