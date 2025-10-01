# prn_constants.py

# --- ROS Topics and Services ---
TOPIC_PRIMITIVE_COMMAND = '/planner/msg_primitive_command'
TOPIC_EXECUTOR_FEEDBACK = '/executor/system_service_feedback'
ACTION_COMPLEX_COMMAND = '/planner/act_complex_command'
SERVICE_SIMPLE_COMMAND = '/planner/srv_simple_command'

# --- Logic Constants ---
WAIT_TIMEOUT_SEC = 5.0 # Max time to wait for execution feedback

# --- Kinematic and Planning Constants ---
PLANE_HEIGHT_CLEARANCE = 100.0  # Height for safe travel over the object/table
PICK_HEIGHT_Z = 50.0            # Height to descend to for grasping
RX_DOWN = 180.0                # Tool pitch (downward-facing)
RY_DOWN = 0.0
DEFAULT_SPEED = 50

# A default "home" pose for the robot
HOME_POSE = [135.0, 145.0, -30.0, 180.0, 0.0, 0.0]

# --- State Feedback Colors (R, G, B) ---
COLOR_CLEARANCE = (0, 0, 255)      # Blue
COLOR_APPROACH = (255, 165, 0)     # Orange
COLOR_GRASP = (0, 255, 0)          # Green
COLOR_RELEASE = (255, 0, 0)        # Red
COLOR_HOME = (255, 255, 255)       # White (Idle)
COLOR_ERROR = (255, 0, 0)          # Solid Red for errors
