# MyCobot 280 Pi ROS2 Pick & Place System 

## System Architecture Overview

This is a ROS2 Galactic system for autonomous pick-and-place operations using an ElephantRobotics MyCobot 280 Pi. The system combines computer vision, motion planning, and a PyQt5 GUI for moving small objects (dried plant specimens) between book pages.

### Critical Architecture Patterns

**10-Node Pipeline Design**: Vision pipeline (4 nodes) → GUI command center (1 node) → Motion planner (1 node) → Robot executor (2 nodes) → RViz visualization (3 nodes)

**File Naming Convention**: All files use prefixed acronyms based on their node:

- `vun_*` = vision_undistorter_node
- `vptn_*` = vision_perspective_transformer_node
- `vodn_*` = vision_object_detector_node
- `grcn_*` = gui_robot_controal_node
- `prn_*` = planner_robot_node
- `ren_*` = robot_executor_node
- `rjpn_*` = robot_jointangles_publisher_node


## Development Environment & Dependencies

**Hardware Requirements**: 
- MyCobot 280 Pi robot with Ubuntu 20.04 + ROS2 Galactic
- Development laptop with static IP network connection
- USB webcam with ChArUco calibration data

**Critical Dependencies**:
- `pymycobot==3.4.7` (locked to match robot's firmware)
- OpenCV with contrib modules for computer vision
- PyQt5 for GUI (not Qt6 - compatibility issues)
- `cv_bridge` for ROS↔OpenCV image conversion

**Build System**: Standard ROS2 colcon with Python setuptools. Interface package uses ament_cmake.

## Key Development Workflows

### Essential Commands Sequence
```bash
# Always check camera first
v4l2-ctl --list-devices


### Node Communication Patterns

**Topic Namespaces Map to Data Flow**:
- `/camera/*` = Raw USB camera data
- `/vision/*` = Processed images and detections  
- `/gui/*` = User interaction data (perspective points)
- `/robot/*` = Physical robot state
- `/planner/*` = Motion commands and coordination

**Service vs Action Usage**:
- **Services**: Simple robot commands (move to point, toggle vacuum)
- **Actions**: Complex multi-step tasks (full pick-and-place sequence with progress feedback)

## Project-Specific Patterns

### Computer Vision Pipeline Quirks
- **Coordinate System Issues**: GUI uses graphics coordinates (y-axis flipped, origin top-left) vs. standard Cartesian
- **Calibration Dependency**: All vision nodes require absolute paths to `camera_calibration.yaml` - launch files must use `FindPackageShare`
- **Four-Point Perspective**: GUI publishes draggable corner points for real-time workspace rectification

### Robot Control Architecture
- **Primitive Command Translation**: Planner breaks complex goals into `SimpleCommands` messages
- **State Management**: Robot executor uses finite state machine to prevent command conflicts
- **Emergency Patterns**: GUI can cancel actions mid-execution, robot must return to home position

### GUI Design Philosophy  
- **Game-Inspired UX**: Drag-and-drop workspace editing inspired by strategy games
- **Multi-Panel Architecture**: Camera preview, workspace editor, control buttons, joint angle monitoring
- **Book Interaction Zone**: Special workspace inside the drag-and-drop workspace area for page-flipping operations (specific to plant specimen use case)


## Integration Points

**URDF + RViz2**: Robot description requires `xacro` processing: `XACROED=$(xacro [urdf_file])` then pass to `robot_state_publisher_node`

**Camera Hardware**: Device paths change (`/dev/video0` vs `/dev/video3`) - always verify with `v4l2-ctl --list-devices`

**Cross-Package Dependencies**: `mycobot280pi_interfaces` must build first - contains all custom message definitions used system-wide

## Anti-Patterns to Avoid

- Don't combine ROS communication with domain logic in same file
- Don't attempt joint movements without checking robot state first  
- Don't use generic ROS message types where custom interfaces exist
- Don't skip the camera calibration step (vision pipeline breaks completely)

When extending this system, maintain the clear node separation, and prefix naming convention.