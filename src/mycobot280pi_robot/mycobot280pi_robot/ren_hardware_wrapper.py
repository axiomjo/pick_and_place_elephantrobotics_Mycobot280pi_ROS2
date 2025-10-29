
import rclpy
from rclpy.node import Node
import math
import time
import RPi.GPIO as GPIO # Required for VacuumPumpV2Controller
from pymycobot import MyCobot, PI_PORT, PI_BAUD # Required for robot control


# ==================================================================
# ### MYCOBOT ERROR CODE MAPPING ###
# ==================================================================
ERROR_CODE_MAPPING = {
    0:  "NO ERROR: Command executed successfully.",
    1:  "JOINT 1: Exceeded angular limit.",
    2:  "JOINT 2: Exceeded angular limit.",
    3:  "JOINT 3: Exceeded angular limit.",
    4:  "JOINT 4: Exceeded angular limit.",
    5:  "JOINT 5: Exceeded angular limit.",
    6:  "JOINT 6: Exceeded angular limit.",
    16: "COLLISION: Collision protection triggered.",
    17: "COLLISION: Collision protection triggered.",
    18: "COLLISION: Collision protection triggered.",
    19: "COLLISION: Collision protection triggered.",
    32: "IK NO SOLUTION: Target coordinates unreachable.",
    33: "LINEAR PATH FAIL: Path obstructed or impossible.",
    34: "LINEAR PATH FAIL: Path obstructed or impossible.",
}






# ==================================================================
# ### HELPER CLASS: Vacuum Pump (Integrated) ###
# ==================================================================
class VacuumPumpV2Controller:
    """Controls the vacuum pump and vent using RPi.GPIO."""
    def __init__(self, pin_pump=21, pin_vent=20, logger=None):
        self.pin_pump = pin_pump
        self.pin_vent = pin_vent
        self.logger = logger
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin_pump, GPIO.OUT)
            GPIO.setup(self.pin_vent, GPIO.OUT)
            self.vacuum_off() # Default off
            
        except Exception as e:
            self._warn(f"GPIO setup failed (Are you on a Pi?): {e}")
    
    def _info(self, msg):
        if self.logger:
            self.logger.info(msg)

    def _warn(self, msg):
        if self.logger:
            self.logger.warn(msg)
            
    def set_state(self, state_pump, state_vent):
        """Sets the state of the vacuum pump and vent pins (0=ON, 1=OFF for active low)."""
        try:
            GPIO.output(self.pin_pump, state_pump)
            GPIO.output(self.pin_vent, state_vent)
            self._info(f"Vacuum state set: pump={state_pump}, vent={state_vent}")
        except Exception as e:
            self._warn(f"Failed to set vacuum state: {e}")

    def vacuum_off(self): 
        self.set_state(1, 1) 
        
    def vacuum_strong(self): 
        self.set_state(0, 1)
        
    def vacuum_weak(self): 
        self.set_state(0, 0)

    def cleanup(self):
        """Cleans up the GPIO pins."""
        try:
            # Only clean up if GPIO mode was set successfully
            if GPIO.getmode() is not None:
                GPIO.cleanup([self.pin_pump, self.pin_vent])
        except Exception:
            pass




class MycobotHardwareWrapper:
    """
    Handles the direct hardware connection and execution of all primitive commands.
    """
    def __init__(self, logger):
        self.logger = logger
        self.mc = self._connect_to_mycobot()
        self.vacuum = VacuumPumpV2Controller(logger=self.logger) 

    def _connect_to_mycobot(self):
        try:
            self.logger.info(f"Connecting to MyCobot on port: {PI_PORT}, baud: {PI_BAUD}")
            mc = MyCobot(PI_PORT, PI_BAUD)
            return mc
        except Exception as e:
            self.logger.error(f"FATAL: Failed to connect to MyCobot: {e}")
            return None

    def execute_command(self, command_type, coords=None, joint_angles=None, speed=50, r=0, g=0, b=0):
        """Executes a command and checks robot error state afterward."""
        if not self.mc:
            return self._fail("MyCobot not connected.")

        try:
            # --- 1. Execute the command ---
            if command_type == "move":
                self.logger.info(f"EXECUTOR: Move to {coords}")
                self.mc.send_coords(list(coords), speed, 1)
                message = "Move command sent asynchronously."

            elif command_type == "move_joints":
                self.logger.info(f"EXECUTOR: Move joints to {joint_angles}")
                self.mc.send_angles(list(joint_angles), speed)
                message = "Joint move command sent."

            elif command_type == "vacuum_strong":
                self.logger.info("EXECUTOR: VACUUM STRONG")
                self.vacuum.vacuum_strong()
                message = "Vacuum STRONG activated."

            elif command_type == "vacuum_weak":
                self.logger.info("EXECUTOR: VACUUM WEAK")
                self.vacuum.vacuum_weak()
                message = "Vacuum WEAK activated."

            elif command_type == "vacuum_off":
                self.logger.info("EXECUTOR: VACUUM OFF")
                self.vacuum.vacuum_off()
                message = "Vacuum OFF executed."

            elif command_type == "set_rgb":
                self.logger.info(f"EXECUTOR: Set RGB ({r}, {g}, {b})")
                self.mc.set_color(r, g, b)
                message = "LED color set successfully."

            else:
                return self._fail(f"Unknown command: {command_type}")

        except Exception as e:
            return self._fail(f"Internal Python exception: {e}")

        # --- 2. Check robot error code ---
        try:
            error_code = self.mc.get_error_information()
            self.mc.clear_error_information()
        except Exception as e:
            return self._fail(f"Failed reading/clearing robot error register: {e}")

        if error_code is None:
            return self._fail("Robot error code returned None (communication issue).")

        if error_code != 0:
            error_string = ERROR_CODE_MAPPING.get(
                error_code, f"UNKNOWN HARDWARE ERROR (Code: {error_code})"
            )
            return self._fail(error_string)

        return True, message

    def get_joint_angles(self):
        """Returns current joint angles or None if unavailable."""
        if not self.mc:
            return None
        try:
            angles = self.mc.get_angles()
            if angles and len(angles) == 6:
                return angles
            return None
        except Exception as e:
            self.logger.warn(f"Failed to get joint states: {e}")
            return None

    def cleanup_hardware(self):
        """Clean up all hardware safely."""
        try:
            self.vacuum.cleanup()
        except Exception as e:
            self.logger.warn(f"Cleanup failed: {e}")

      
    def _fail(self, msg):
        """Unified error return + log."""
        self.logger.warn(f"EXECUTOR: {msg}")
        return False, f"Command failed: {msg}"
