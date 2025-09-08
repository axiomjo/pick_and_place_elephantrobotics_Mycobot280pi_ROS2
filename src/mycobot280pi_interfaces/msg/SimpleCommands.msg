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

# For vacuum or gripper commands, you can add more fields as needed

# For future extensibility, you can add:
string[] extra_strings     # For any extra string parameters
float32[] extra_floats     # For any extra float parameters
int32[] extra_ints         # For any extra int parameters
