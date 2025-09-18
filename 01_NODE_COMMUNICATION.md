
[19 sept 04:28]

This document details the architecture of the MyCobot 280 Pi ROS2 system. The system is composed of several nodes responsible for vision processing, user interface, motion planning, and robot control.

# ==== 01 : NODE COMMUNICATION =======

## NODE DETAILS

### **1. `vision_usb_cam_node` (Pre-built Package) 📸**

  * **Functionality:** This node acts as the primary image source for the entire vision pipeline. It captures raw image frames directly from a connected USB webcam and publishes them for further processing.
  * **Parameters:**
      * `video_device` (`string`): The file system path to the USB camera device (e.g., `/dev/video0`).
      * `camera_name` (`string`): A unique name for the camera, used as its frame ID in the TF tree.
  * **Communication Interfaces:**
      * **Publisher:**
          * **Topic:** `/camera/msg_image_raw`
          * **Type:** `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Publishes a continuous stream of raw, distorted images from the webcam to the `vision_undistorter_node`.
          * **ros2 interface show sensor\_msgs/msg/Image:**
            ```plaintext
            # This message contains an uncompressed image
            # (0, 0) is at top-left corner of image

            std_msgs/Header header # Header timestamp should be acquisition time of image
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id
                                         # Header frame_id should be optical frame of camera
                                         # origin of frame should be optical center of cameara
                                         # +x should point to the right in the image
                                         # +y should point down in the image
                                         # +z should point into to plane of the image
                                         # If the frame_id here and the frame_id of the CameraInfo
                                         # message associated with the image conflict
                                         # the behavior is undefined

            uint32 height                # image height, that is, number of rows
            uint32 width                 # image width, that is, number of columns

            # The legal values for encoding are in file src/image_encodings.cpp
            # If you want to standardize a new string format, join
            # ros-users@lists.ros.org and send an email proposing a new encoding.

            string encoding       # Encoding of pixels -- channel meaning, ordering, size
                                  # taken from the list of strings in include/sensor_msgs/image_encodings.hpp

            uint8 is_bigendian    # is this data bigendian?
            uint32 step           # Full row length in bytes
            uint8[] data          # actual matrix data, size is (step * rows)
            ```

-----

### **2. `vision_undistorter_node` 🛠️**

  * **Functionality:** Corrects for lens barrel distortion in the raw image stream. It subscribes to the raw images, applies a correction based on a provided camera calibration file, and publishes the rectified images.
  * **Parameters:**
      * `camera_info_file` (`string`): The absolute path to the `.yaml` file containing the camera's intrinsic calibration matrix and distortion coefficients.
  * **Communication Interfaces:**
      * **Subscriber:**
          * **Topic:** `/camera/msg_image_raw`
          * **Type:** `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Receives the raw image stream from `vision_usb_cam_node`.
          * **ros2 interface show sensor\_msgs/msg/Image:**
            ```plaintext
            # This message contains an uncompressed image
            # (0, 0) is at top-left corner of image

            std_msgs/Header header # Header timestamp should be acquisition time of image
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id
                                         # Header frame_id should be optical frame of camera
                                         # origin of frame should be optical center of cameara
                                         # +x should point to the right in the image
                                         # +y should point down in the image
                                         # +z should point into to plane of the image
                                         # If the frame_id here and the frame_id of the CameraInfo
                                         # message associated with the image conflict
                                         # the behavior is undefined

            uint32 height                # image height, that is, number of rows
            uint32 width                 # image width, that is, number of columns

            # The legal values for encoding are in file src/image_encodings.cpp
            # If you want to standardize a new string format, join
            # ros-users@lists.ros.org and send an email proposing a new encoding.

            string encoding       # Encoding of pixels -- channel meaning, ordering, size
                                  # taken from the list of strings in include/sensor_msgs/image_encodings.hpp

            uint8 is_bigendian    # is this data bigendian?
            uint32 step           # Full row length in bytes
            uint8[] data          # actual matrix data, size is (step * rows)
            ```
      * **Publisher:**
          * **Topic:** `/vision/msg_undistorted_image`
          * **Type:** `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Publishes the corrected, undistorted image stream to `vision_perspective_transformer_node` and `gui_robot_control_node`.
          * **ros2 interface show sensor\_msgs/msg/Image:**
            ```plaintext
            # This message contains an uncompressed image
            # (0, 0) is at top-left corner of image

            std_msgs/Header header # Header timestamp should be acquisition time of image
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id
                                         # Header frame_id should be optical frame of camera
                                         # origin of frame should be optical center of cameara
                                         # +x should point to the right in the image
                                         # +y should point down in the image
                                         # +z should point into to plane of the image
                                         # If the frame_id here and the frame_id of the CameraInfo
                                         # message associated with the image conflict
                                         # the behavior is undefined

            uint32 height                # image height, that is, number of rows
            uint32 width                 # image width, that is, number of columns

            # The legal values for encoding are in file src/image_encodings.cpp
            # If you want to standardize a new string format, join
            # ros-users@lists.ros.org and send an email proposing a new encoding.

            string encoding       # Encoding of pixels -- channel meaning, ordering, size
                                  # taken from the list of strings in include/sensor_msgs/image_encodings.hpp

            uint8 is_bigendian    # is this data bigendian?
            uint32 step           # Full row length in bytes
            uint8[] data          # actual matrix data, size is (step * rows)
            ```

-----

### **3. `vision_perspective_transformer_node` 📐**

  * **Functionality:** Transforms the undistorted image to a top-down "bird's-eye view" of the workspace. It uses a set of four points provided by the GUI to perform the perspective warp.
  * **Communication Interfaces:**
      * **Subscriber 1:**
          * **Topic:** `/vision/msg_undistorted_image`
          * **Type:** `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Receives the undistorted image stream from `vision_undistorter_node`.
          * **ros2 interface show sensor\_msgs/msg/Image:**
            ```plaintext
            # This message contains an uncompressed image
            # (0, 0) is at top-left corner of image

            std_msgs/Header header # Header timestamp should be acquisition time of image
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id
                                         # Header frame_id should be optical frame of camera
                                         # origin of frame should be optical center of cameara
                                         # +x should point to the right in the image
                                         # +y should point down in the image
                                         # +z should point into to plane of the image
                                         # If the frame_id here and the frame_id of the CameraInfo
                                         # message associated with the image conflict
                                         # the behavior is undefined

            uint32 height                # image height, that is, number of rows
            uint32 width                 # image width, that is, number of columns

            # The legal values for encoding are in file src/image_encodings.cpp
            # If you want to standardize a new string format, join
            # ros-users@lists.ros.org and send an email proposing a new encoding.

            string encoding       # Encoding of pixels -- channel meaning, ordering, size
                                  # taken from the list of strings in include/sensor_msgs/image_encodings.hpp

            uint8 is_bigendian    # is this data bigendian?
            uint32 step           # Full row length in bytes
            uint8[] data          # actual matrix data, size is (step * rows)
            ```
      * **Subscriber 2:**
          * **Topic:** `/gui/msg_four_perspective_points`
          * **Type:** `mycobot280pi_interfaces/msg/Point2DArray`
          * **Description:** Receives an array of four coordinate points from `gui_robot_control_node` to define the perspective transformation.
          * **ros2 interface show mycobot280pi\_interfaces/msg/Point2DArray:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/msg/Point2DArray.msg

            # This part is the message definition
            mycobot280pi_interfaces/Point2D[] points
            ```
      * **Publisher:**
          * **Topic:** `/vision/msg_top_down_image`
          * **Type:** `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Publishes the resulting top-down image to `vision_object_detector_node` and `gui_robot_control_node`.
          * **ros2 interface show sensor\_msgs/msg/Image:**
            ```plaintext
            # This message contains an uncompressed image
            # (0, 0) is at top-left corner of image

            std_msgs/Header header # Header timestamp should be acquisition time of image
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id
                                         # Header frame_id should be optical frame of camera
                                         # origin of frame should be optical center of cameara
                                         # +x should point to the right in the image
                                         # +y should point down in the image
                                         # +z should point into to plane of the image
                                         # If the frame_id here and the frame_id of the CameraInfo
                                         # message associated with the image conflict
                                         # the behavior is undefined

            uint32 height                # image height, that is, number of rows
            uint32 width                 # image width, that is, number of columns

            # The legal values for encoding are in file src/image_encodings.cpp
            # If you want to standardize a new string format, join
            # ros-users@lists.ros.org and send an email proposing a new encoding.

            string encoding       # Encoding of pixels -- channel meaning, ordering, size
                                  # taken from the list of strings in include/sensor_msgs/image_encodings.hpp

            uint8 is_bigendian    # is this data bigendian?
            uint32 step           # Full row length in bytes
            uint8[] data          # actual matrix data, size is (step * rows)
            ```

-----

### **4. `vision_object_detector_node` 🎯**

  * **Functionality:** Detects objects (blobs) within the top-down workspace view. It processes the incoming image, identifies objects, calculates their bounding boxes and center points, and publishes both the detection data and an annotated image.
  * **Communication Interfaces:**
      * **Subscriber:**
          * **Topic:** `/vision/msg_top_down_image`
          * **Type:** `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Receives the top-down image from `vision_perspective_transformer_node`.
          * **ros2 interface show sensor\_msgs/msg/Image:**
            ```plaintext
            # This message contains an uncompressed image
            # (0, 0) is at top-left corner of image

            std_msgs/Header header # Header timestamp should be acquisition time of image
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id
                                         # Header frame_id should be optical frame of camera
                                         # origin of frame should be optical center of cameara
                                         # +x should point to the right in the image
                                         # +y should point down in the image
                                         # +z should point into to plane of the image
                                         # If the frame_id here and the frame_id of the CameraInfo
                                         # message associated with the image conflict
                                         # the behavior is undefined

            uint32 height                # image height, that is, number of rows
            uint32 width                 # image width, that is, number of columns

            # The legal values for encoding are in file src/image_encodings.cpp
            # If you want to standardize a new string format, join
            # ros-users@lists.ros.org and send an email proposing a new encoding.

            string encoding       # Encoding of pixels -- channel meaning, ordering, size
                                  # taken from the list of strings in include/sensor_msgs/image_encodings.hpp

            uint8 is_bigendian    # is this data bigendian?
            uint32 step           # Full row length in bytes
            uint8[] data          # actual matrix data, size is (step * rows)
            ```
      * **Publisher 1:**
          * **Topic:** `/vision/msg_detected_objects`
          * **Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
          * **Description:** Publishes an array of detected objects, including their positions and properties, to `gui_robot_control_node`.
          * **ros2 interface show mycobot280pi\_interfaces/msg/ManyDetectedObjects:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/msg/ManyDetectedObjects.msg

            # This part is the message definition
            std_msgs/Header header
            mycobot280pi_interfaces/OneDetectedObject[] objects
            ```
      * **Publisher 2:**
          * **Topic:** `/vision/msg_annotated_image`
          * **Type:** `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Publishes the top-down image with visual annotations (e.g., bounding boxes) drawn on it for display in the `gui_robot_control_node`.
          * **ros2 interface show sensor\_msgs/msg/Image:**
            ```plaintext
            # This message contains an uncompressed image
            # (0, 0) is at top-left corner of image

            std_msgs/Header header # Header timestamp should be acquisition time of image
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id
                                         # Header frame_id should be optical frame of camera
                                         # origin of frame should be optical center of cameara
                                         # +x should point to the right in the image
                                         # +y should point down in the image
                                         # +z should point into to plane of the image
                                         # If the frame_id here and the frame_id of the CameraInfo
                                         # message associated with the image conflict
                                         # the behavior is undefined

            uint32 height                # image height, that is, number of rows
            uint32 width                 # image width, that is, number of columns

            # The legal values for encoding are in file src/image_encodings.cpp
            # If you want to standardize a new string format, join
            # ros-users@lists.ros.org and send an email proposing a new encoding.

            string encoding       # Encoding of pixels -- channel meaning, ordering, size
                                  # taken from the list of strings in include/sensor_msgs/image_encodings.hpp

            uint8 is_bigendian    # is this data bigendian?
            uint32 step           # Full row length in bytes
            uint8[] data          # actual matrix data, size is (step * rows)
            ```

-----

### **5. `gui_robot_control_node` 💻**

  * **Functionality:** The central command and control interface for the user. It displays various image streams, allows interactive editing of the perspective transform and the robot's workspace, sends commands to the robot, and reports the robot's state.
  * **Communication Interfaces:**
      * **Subscriber 1:**
          * **Topic:** `/vision/msg_undistorted_image`
          * **Type:** `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Receives the undistorted image from `vision_undistorter_node` for the perspective editing view.
          * **ros2 interface show sensor\_msgs/msg/Image:**
            ```plaintext
            # This message contains an uncompressed image
            # (0, 0) is at top-left corner of image

            std_msgs/Header header # Header timestamp should be acquisition time of image
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id
                                         # Header frame_id should be optical frame of camera
                                         # origin of frame should be optical center of cameara
                                         # +x should point to the right in the image
                                         # +y should point down in the image
                                         # +z should point into to plane of the image
                                         # If the frame_id here and the frame_id of the CameraInfo
                                         # message associated with the image conflict
                                         # the behavior is undefined

            uint32 height                # image height, that is, number of rows
            uint32 width                 # image width, that is, number of columns

            # The legal values for encoding are in file src/image_encodings.cpp
            # If you want to standardize a new string format, join
            # ros-users@lists.ros.org and send an email proposing a new encoding.

            string encoding       # Encoding of pixels -- channel meaning, ordering, size
                                  # taken from the list of strings in include/sensor_msgs/image_encodings.hpp

            uint8 is_bigendian    # is this data bigendian?
            uint32 step           # Full row length in bytes
            uint8[] data          # actual matrix data, size is (step * rows)
            ```
      * **Subscriber 2:**
          * **Topic:** `/vision/msg_detected_objects`
          * **Type:** `mycobot280pi_interfaces/msg/ManyDetectedObjects`
          * **Description:** Receives object data from `vision_object_detector_node` to populate the interactive workspace.
          * **ros2 interface show mycobot280pi\_interfaces/msg/ManyDetectedObjects:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/msg/ManyDetectedObjects.msg

            # This part is the message definition
            std_msgs/Header header
            mycobot280pi_interfaces/OneDetectedObject[] objects
            ```
      * **Subscriber 3:**
          * **Topic:** `/vision/msg_annotated_image`
          * **Type:** `sensor_msgs/msg/Image` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Receives the annotated image from `vision_object_detector_node` for display.
          * **ros2 interface show sensor\_msgs/msg/Image:**
            ```plaintext
            # This message contains an uncompressed image
            # (0, 0) is at top-left corner of image

            std_msgs/Header header # Header timestamp should be acquisition time of image
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id
                                         # Header frame_id should be optical frame of camera
                                         # origin of frame should be optical center of cameara
                                         # +x should point to the right in the image
                                         # +y should point down in the image
                                         # +z should point into to plane of the image
                                         # If the frame_id here and the frame_id of the CameraInfo
                                         # message associated with the image conflict
                                         # the behavior is undefined

            uint32 height                # image height, that is, number of rows
            uint32 width                 # image width, that is, number of columns

            # The legal values for encoding are in file src/image_encodings.cpp
            # If you want to standardize a new string format, join
            # ros-users@lists.ros.org and send an email proposing a new encoding.

            string encoding       # Encoding of pixels -- channel meaning, ordering, size
                                  # taken from the list of strings in include/sensor_msgs/image_encodings.hpp

            uint8 is_bigendian    # is this data bigendian?
            uint32 step           # Full row length in bytes
            uint8[] data          # actual matrix data, size is (step * rows)
            ```
      * **Subscriber 4:**
          * **Topic:** `/robot/msg_joint_angles`
          * **Type:** `sensor_msgs/msg/JointState` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Receives real-time joint angles from `mycobot_jointangles_publisher_node` for monitoring.
          * **ros2 interface show sensor\_msgs/msg/JointState**
            ```plaintext
            # This is a message that holds data to describe the state of a set of torque controlled joints.
            #
            # The state of each joint (revolute or prismatic) is defined by:
            #  * the position of the joint (rad or m),
            #  * the velocity of the joint (rad/s or m/s) and
            #  * the effort that is applied in the joint (Nm or N).
            #
            # Each joint is uniquely identified by its name
            # The header specifies the time at which the joint states were recorded. All the joint states
            # in one message have to be recorded at the same time.
            #
            # This message consists of a multiple arrays, one for each part of the joint state.
            # The goal is to make each of the fields optional. When e.g. your joints have no
            # effort associated with them, you can leave the effort array empty.
            #
            # All arrays in this message should have the same size, or be empty.
            # This is the only way to uniquely associate the joint name with the correct
            # states.

            std_msgs/Header header
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id

            string[] name
            float64[] position
            float64[] velocity
            float64[] effort
            ```
      * **Publisher:**
          * **Topic:** `/gui/msg_four_perspective_points`
          * **Type:** `mycobot280pi_interfaces/msg/Point2DArray`
          * **Description:** Publishes the four points selected by the user for the perspective transform to `vision_perspective_transformer_node`.
          * **ros2 interface show mycobot280pi\_interfaces/msg/Point2DArray:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/msg/Point2DArray.msg

            # This part is the message definition
            mycobot280pi_interfaces/Point2D[] points
            ```
      * **Service Client:**
          * **Service:** `/planner/srv_simple_command`
          * **Type:** `mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure`
          * **Description:** Sends requests for simple, discrete actions (e.g., "activate pump") to `planner_robot_node`.
          * **ros2 interface show mycobot280pi\_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure.srv

            # This part is the request
            float32[] coords
            int32 speed
            bool is_linear_mode
            ---
            # This part is the response
            bool success
            string message
            ```
      * **Action Client:**
          * **Action:** `/planner/act_complex_command`
          * **Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`
          * **Description:** Sends goals for complex, multi-step tasks (e.g., rearranging objects) to `planner_robot_node` and receives continuous feedback on the progress.
          * **ros2 interface show mycobot280pi\_interfaces/action/ProcessWorkspace:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/action/ProcessWorkspace.action

            # This part is the goal
            mycobot280pi_interfaces/ManyDetectedObjects objects_to_move
            mycobot280pi_interfaces/Point2DArray objects_target_position
            int32[] objects_target_orientation
            ---
            # This part is the result
            bool success
            string message
            ---
            # This part is the feedback
            string current_state
            mycobot280pi_interfaces/OneDetectedObject current_object
            ```

-----

### **6. `planner_robot_node` 🤖**

  * **Functionality:** The "brain" of the robot. It receives high-level commands from the GUI and breaks them down into a sequence of simple, primitive robot movements. It handles both immediate commands (via services) and long-running tasks (via actions).
  * **Communication Interfaces:**
      * **Service Server:**
          * **Service:** `/planner/srv_simple_command`
          * **Type:** `mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure`
          * **Description:** Handles simple command requests from `gui_robot_control_node`.
          * **ros2 interface show mycobot280pi\_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/srv/Mycobot280PiSimpleCommandsMadeSure.srv

            # This part is the request
            float32[] coords
            int32 speed
            bool is_linear_mode
            ---
            # This part is the response
            bool success
            string message
            ```
      * **Action Server:**
          * **Action:** `/planner/act_complex_command`
          * **Type:** `mycobot280pi_interfaces/action/ProcessWorkspace`
          * **Description:** Handles complex task goals from `gui_robot_control_node`, executing the plan and providing feedback.
          * **ros2 interface show mycobot280pi\_interfaces/action/ProcessWorkspace:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/action/ProcessWorkspace.action

            # This part is the goal
            mycobot280pi_interfaces/ManyDetectedObjects objects_to_move
            mycobot280pi_interfaces/Point2DArray objects_target_position
            int32[] objects_target_orientation
            ---
            # This part is the result
            bool success
            string message
            ---
            # This part is the feedback
            string current_state
            mycobot280pi_interfaces/OneDetectedObject current_object
            ```
      * **Publisher:**
          * **Topic:** `/planner/msg_primitive_command`
          * **Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
          * **Description:** Publishes the sequence of low-level commands (e.g., "move to coordinates") to `mycobot_executor_node`.
          * **ros2 interface show mycobot280pi\_interfaces/msg/SimpleCommands:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/msg/SimpleCommands.msg

            # This part is the message definition
            string command_type

            float32[] coords
            float32[] joint_angles
            int32 speed

            int32 r
            int32 g
            int32 b

            string[] extra_strings
            float32[] extra_floats
            int32[] extra_ints
            ```

-----

### **7. `mycobot_executor_node` 🏃**

  * **Functionality:** The direct interface to the robot hardware. This node subscribes to primitive commands and translates them into the specific `pymycobot` API calls required to make the physical robot move.
  * **Communication Interfaces:**
      * **Subscriber:**
          * **Topic:** `/planner/msg_primitive_command`
          * **Type:** `mycobot280pi_interfaces/msg/SimpleCommands`
          * **Description:** Receives low-level commands from `planner_robot_node`.
          * **ros2 interface show mycobot280pi\_interfaces/msg/SimpleCommands:**
            ```plaintext
            # Filepath: src/mycobot280pi_interfaces/msg/SimpleCommands.msg

            # This part is the message definition
            string command_type

            float32[] coords
            float32[] joint_angles
            int32 speed

            int32 r
            int32 g
            int32 b

            string[] extra_strings
            float32[] extra_floats
            int32[] extra_ints
            ```

-----

### **8. `mycobot_jointangles_publisher_node` 🦾**

  * **Functionality:** Continuously queries the robot's hardware for the current angle of each of its six joints and publishes this information for use by other nodes.
  * **Communication Interfaces:**
      * **Publisher:**
          * **Topic:** `/robot/msg_joint_angles`
          * **Type:** `sensor_msgs/msg/JointState` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Publishes the robot's current joint states to `gui_robot_control_node`.
          * **ros2 interface show sensor\_msgs/msg/JointState**
            ```plaintext
            # This is a message that holds data to describe the state of a set of torque controlled joints.
            #
            # The state of each joint (revolute or prismatic) is defined by:
            #  * the position of the joint (rad or m),
            #  * the velocity of the joint (rad/s or m/s) and
            #  * the effort that is applied in the joint (Nm or N).
            #
            # Each joint is uniquely identified by its name
            # The header specifies the time at which the joint states were recorded. All the joint states
            # in one message have to be recorded at the same time.
            #
            # This message consists of a multiple arrays, one for each part of the joint state.
            # The goal is to make each of the fields optional. When e.g. your joints have no
            # effort associated with them, you can leave the effort array empty.
            #
            # All arrays in this message should have the same size, or be empty.
            # This is the only way to uniquely associate the joint name with the correct
            # states.

            std_msgs/Header header
                builtin_interfaces/Time stamp
                    int32 sec
                    uint32 nanosec
                string frame_id

            string[] name
            float64[] position
            float64[] velocity
            float64[] effort
            ```

-----

### **9. `mycobot_state_publisher_node` (Pre-built Package) 📝**

  * **Functionality:** Publishes the robot's static and dynamic state as TF (Transform) messages. It uses the robot's URDF model and joint states to compute the position and orientation of each link, primarily for visualization in RViz2.
  * **Parameters:**
      * `robot_description` (`string`): The robot's complete URDF model as a string.
  * **Communication Interfaces:**
      * **Publisher 1:**
          * **Topic:** `/rviz2/tf_static`
          * **Type:** `tf2_msgs/msg/TFMessage` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Publishes the static transforms (fixed relationships between robot links) to `ui_rviz2_node`.
      * **Publisher 2:**
          * **Topic:** `/rviz2/tf`
          * **Type:** `tf2_msgs/msg/TFMessage` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Publishes the dynamic transforms (changing relationships based on joint angles) to `ui_rviz2_node`.

-----

### **10. `ui_rviz2_node` (Pre-built Package) 🖼️**

  * **Functionality:** A powerful 3D visualization tool. It subscribes to transform data and other topics to display a live, 3D model of the robot and its environment.
  * **Communication Interfaces:**
      * **Subscriber 1:**
          * **Topic:** `/rviz2/tf_static`
          * **Type:** `tf2_msgs/msg/TFMessage` \[BUILTIN ROS2 INTERFACE]
          * **Description:** Receives static transforms from `mycobot_state_publisher_node`.
      * **Subscriber 2:**
          * **Topic:** `/rviz2/tf`
          * **Type:** `tf2_msgs/msg/TFMessage`\[BUILTIN ROS2 INTERFACE]
          * **Description:** Receives dynamic transforms from `mycobot_state_publisher_node`.

-----

