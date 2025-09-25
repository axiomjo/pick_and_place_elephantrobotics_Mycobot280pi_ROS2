"""
ren_robot_state_manager.py

Tracks the robot's current state, manages task sequences, and coordinates with MyCobotAPI.
"""

class RobotStateManager:
    def __init__(self, logger):
        self.logger = logger
        self.state = "idle"
        self.task_step = None
        self.task_sequence = []
        self.error_msg = ""

    def set_state(self, new_state):
        self.state = new_state
        self.logger.info(f"Robot state updated to: {new_state}")

    def get_state(self):
        return self.state

    def start_task(self, task_sequence):
        """
        Begin a multi-step task (e.g., pick and place, page turn).
        task_sequence: list of dicts, each with 'action' and params.
        """
        self.task_sequence = task_sequence
        self.task_step = 0
        self.set_state("running_task")

    def next_step(self):
        """
        Proceed to the next step in the current task.
        Returns the action dict, or None if done.
        """
        if self.task_sequence and self.task_step is not None:
            if self.task_step < len(self.task_sequence):
                action = self.task_sequence[self.task_step]
                self.task_step += 1
                return action
            else:
                self.set_state("idle")
                self.task_step = None
                self.task_sequence = []
                return None
        return None

    def set_error(self, msg):
        self.state = "error"
        self.error_msg = msg
        self.logger.error(f"Robot error: {msg}")

    def clear_error(self):
        self.state = "idle"
        self.error_msg = ""
        self.logger.info("Error cleared, state set to idle.")
