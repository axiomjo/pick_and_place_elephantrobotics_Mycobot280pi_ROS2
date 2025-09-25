"""
rmen_mycobot_interface.py

Encapsulates pymycobot API calls and GPIO-based vacuum pump control for robot control.
"""

from pymycobot import MyCobot, PI_PORT, PI_BAUD
import RPi.GPIO as GPIO

class VacuumPumpV2Controller:
    """
    Controls the Vacuum Pump V2.0 using two GPIO pins.
    You can assign any available GPIO pins for pump and vent.
    """
    def __init__(self, pin_pump=21, pin_vent=20, logger=None):
        self.pin_pump = pin_pump
        self.pin_vent = pin_vent
        self.logger = logger
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_pump, GPIO.OUT)
        GPIO.setup(self.pin_vent, GPIO.OUT)
        self.set_state(1, 1)  # Default: Off

    def set_state(self, state_pump, state_vent):
        GPIO.output(self.pin_pump, state_pump)
        GPIO.output(self.pin_vent, state_vent)
        desc = self.describe_state(state_pump, state_vent)
        if self.logger:
            self.logger.info(f"Vacuum Pump set: PUMP={state_pump}, VENT={state_vent} ({desc})")

    def vacuum_off(self):
        self.set_state(1, 1)

    def vacuum_strong(self):
        self.set_state(0, 1)

    def vacuum_weak(self):
        self.set_state(0, 0)

    @staticmethod
    def describe_state(state_pump, state_vent):
        if state_pump == 1:
            return "Off"
        elif state_pump == 0 and state_vent == 1:
            return "Strong Vacuum"
        elif state_pump == 0 and state_vent == 0:
            return "Weak Vacuum"
        else:
            return "Unknown"

    def cleanup(self):
        GPIO.cleanup([self.pin_pump, self.pin_vent])

class MyCobotInterface:
    def __init__(self, logger, pin_pump=21, pin_vent=20):
        self.logger = logger
        try:
            self.mc = MyCobot(PI_PORT, PI_BAUD)
            self.logger.info("Connected to MyCobot.")
        except Exception as e:
            self.logger.error(f"Failed to connect to MyCobot: {e}")
            self.mc = None

        # Initialize vacuum pump controller with configurable pins
        self.vacuum = VacuumPumpV2Controller(pin_pump, pin_vent, logger)

    def move_to_coords(self, coords, speed):
        if self.mc:
            try:
                self.mc.send_coords(list(coords), speed, 1)
                self.logger.info(f"Moving to coords: {coords} at speed {speed}")
            except Exception as e:
                self.logger.error(f"Failed to move: {e}")

    def set_rgb(self, r, g, b):
        if self.mc:
            try:
                self.mc.set_color(r, g, b)
                self.logger.info(f"Set RGB color to ({r}, {g}, {b})")
            except Exception as e:
                self.logger.error(f"Failed to set RGB color: {e}")

    # Vacuum pump controls
    def vacuum_off(self):
        self.vacuum.vacuum_off()

    def vacuum_strong(self):
        self.vacuum.vacuum_strong()

    def vacuum_weak(self):
        self.vacuum.vacuum_weak()

    def cleanup(self):
        self.vacuum.cleanup()
