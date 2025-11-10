my_ros_package/
├── ...
├── planner_node.py       (Your PlannerNode class)
└── planner_hsm/          <-- NEW DIRECTORY (This is your package)
    ├── __init__.py       (This file makes it a package)
    ├── hsm_core.py       (Holds the 'definitions')
    ├── hsm_engine.py     (Holds the 'engine')
    ├── hsm_top_states.py   (Holds L1 states)
    ├── hsm_busy_states.py  (Holds L2 states)
    └── hsm_exec_states.py  (Holds L3 execution states)

======================

You've built an **Asynchronous, Event-Driven, 3-Level Hierarchical State Machine (HSM)**.

This architecture uses the **State Design Pattern** to manage its logic and the **Facade Pattern** to cleanly separate that logic from your ROS 2 node.

Here’s a breakdown of the all-encompassing architecture.

## 1. Asynchronous, Event-Driven Core

At its heart, your system is not a simple script that runs from top to bottom. It's an **asynchronous engine** that *reacts* to triggers.

* **Event-Driven:** The machine does *nothing* until an `EventID` (an "arrow") is fired. This is far more efficient than constantly checking "am I done yet?"
* **Asynchronous:** By using `async`/`await`, your "worker" states (like `WAITING_MOVE_DONE`) can pause for long-running tasks (like a 5-second robot move) *without* freezing the entire ROS node. This allows the system to remain "completionist" and instantly react to a global `CANCEL` or `ERROR` event even while it's in the middle of a "wait."

---

## 2. Clean Separation of Concerns (The Facade)

You have two distinct "layers" that talk to each other through a clean interface. This is the **Facade Pattern**.

* **The "ROS Layer" (`PlannerNode`):** This class is the "translator." It speaks ROS. Its only job is to handle ROS actions, clients, and feedback. It **does not know** the *logic* of your process (e.g., that `FETCH` comes before `SEND`). It just translates ROS data into HSM events (like `EventID.NEW_GOAL`).
* **The "Logic Layer" (`PlannerHSM`):** This is the "brain." It is the **Facade** for your state machine. It speaks your *process*. It has no idea what a ROS "action client" is, but it knows that after `PLANNING` it must go to `EXECUTING`.

---

## 3. 3-Level Hierarchical Encapsulation

This is the most important part—your "Good Practice" 3-level design. It prevents "God Nodes" by encapsulating logic at the correct level.

* **Level 1: The "General Manager" (`BusyState`)**
    * This is your `BUSY` box.
    * Its code is **clean and simple**.
    * Its only job is to handle the two "global" events (`CANCEL`, `ERROR`) that all its children "inherit."
    * It **delegates** all other work to its "Team Leads."

* **Level 2: The "Team Leads" (`BusyPlanningState`, `BusyExecutingState`)**
    * These are the `PLANNING` and `EXECUTING` boxes.
    * They are "mini-engines" or "specialist managers."
    * The `BusyExecutingState` class is **not** useless—it's the *most important part* for encapsulation. Its one job is to contain the **entire "happy path" logic** for the execution loop (`FETCH` $\to$ `SEND` $\to$ `WAIT` $\to$ `READY`), keeping that complexity out of the "General Manager."

* **Level 3: The "Workers" (`FETCHING_COMMAND`, `SENDING_COMMAND`, etc.)**
    * These are your "leaf" states.
    * They are "specialists" that do one single job and then report to their "Team Lead" (e.g., by returning `BusyExecutingSendCommandState()`).
    * The **"escape" transition** (`queue_emptied` $\to$ `DONE`) is the one case where a "Worker" can bypass its managers to signal the entire job is finished.

  = auto()
     = auto()
     = auto()
     = auto()
     = auto() 
     = auto(
 
class StateID(Enum):
    #auto() is used coz the assigned number doesn't matter, as long as they're unique to each other
    IDLE = auto()
    BUSY = auto()
     = auto()
     = auto()
     = auto() 

    # BUSY superstate's states
    busy_PLANNING = auto()
    busy_EXECUTING = auto()
    busy_RECORDING = auto()
    
    # BUSY EXECUTING's states
    busy_executing_FETCH_COMMAND = auto()
    busy_executing_SEND_COMMAND = auto()
    busy_executing_WAIT = auto()
    busy_executing_WAIT_MOVE_COMPLETE = auto() 
    busy_executing_READY = auto() 
    
    # BUSY RECORDING's state
    busy_recording_START = auto()
    busy_recording_RECORD = auto()
    busy_recording_END = auto()
    busy_recording_SAVE = auto() 
    busy_recording_DELETE = auto()
      
         
 
 
 
 
 
 
 
       
    def is_busy(self):
        """Check if the HSM is available for a new goal."""
        return self.state in [
            State.busy_BUILDING_PLAN,
            State.busy_GETTING_NEXT_COMMAND,
            State.busy_SENDING_COMMAND,
            State.busy_WAITING_FOR_RESULT,
            State.busy_WAITING_FOR_MOVE_COMPLETE
        ]
        
    def handle_new_goal(self, goal_handle):
        """ method for processing complex goal handle """
        
        if self.is_busy():
            # This shouldn't happen if the node's goal_callback is correct
            self.node.get_logger().warn("HSM: Was busy, goal should have been rejected.")
            return
            
        self.node.get_logger().info("HSM: Received new complex goal.")
        self.current_goal_handle = goal_handle
        self.transition_to(State.busy_BUILDING_PLAN)
         
     
    def handle_cancel_request(self):
        """ method for cancelled complex goal handle """
        self.node.get_logger().info("HSM: Received CANCELATION req for complex goal.")
        
        if self.is_busy():
            self.transition_to(State.CANCELLING)
    
    def on_joint_angles_feedback(self,msg):
        """  
        public callback method 
        for seeing if target position is reached  
        """
        
        if self.are_angles_close(msg.joint_angles, self.target_angles);
            self.node.get_logger().info("HSM: Robot move complete.")
            self.transition_to(State.busy_GETTING_NEXT_COMMAND)
    
    
    
    def build_plan_queue(self):
        """ 
        method for breaking down complex command to command primitives.
        
        input:
        
        output: array containing SimpleCommandsAction.goal
        """
        
        self.node.get_logger().info("HSM: Generating PLAN  QUEUE")
        self.plan_queue = []
        request = self.current_goal_handle.request
        
        try:
            objects = request.objects_to_move.objects
            targets = request.objects_target_position.points
            orientations = request.objects_target_orientation
        
            home_goal = SimpleCommandsAction.Goal(
                command_type="move_joints", 
                joint_angles=[0.0] * 6, 
                speed=100
            )
            self.plan_queue.append(home_goal)
            
            RX_DOWN = 180.0
            RY_DOWN = 0.0
            
            
            for i, (obj, target, orient) in enumerate(zip(objects, targets, orientations)):
            
                
    def _get_home_goal(self):
        """Returns a single 'home' goal."""
        return SimpleCommandsAction.Goal(
                command_type="move_joints", 
                joint_angles=[0.0] * 6, 
                speed=100
            )
            
    def _get_pick_sequence(self, point, orientation ):
        """ Returns a list of all actions for pick """
        x,y = point.x, point.y
        rx, ry, rz = orientation
        
        above_pick_coords =[x, y, 70.0, rx, ry, rz]
        pick_coords = [x, y, 30.0, rx, ry, rz]
        
        return [
        
            # 1. Approach
            SimpleCommandsAction.Goal(
                command_type="set_rgb", 
                r=255,  
                g=255, 
                b=0
            ),
            
            SimpleCommandsAction.Goal(
                command_type="move",
                coords=above_pick_coords,
                speed=100
            ),
            
            
            
            # 2. Set for pick
            SimpleCommandsAction.Goal(
                command_type="set_rgb", 
                r=255, 
                g=0, 
                b=0
            ),
            
            SimpleCommandsAction.Goal(
                command_type="vacuum_strong"
            ),
                
            # 3. Descend to pick
            SimpleCommandsAction.Goal(
                command_type="move",
                coords=pick_coords,
                speed=50
            ),
            
            SimpleCommandsAction.Goal(
                command_type="move",
                coords=above_pick_coords,
                speed=100
            ),
        ]
        
        def _get_place_sequence(self, point, orientation):
        """
        Returns a LIST of all primitive commands
        required to perform a "place" operation.
        """
        x, y = point.x, point.y
        rx, ry, rz = orientation
        
        approach_coords = [x, y, 70.0, rx, ry, rz]
        place_coords = [x, y, 30.0, rx, ry, rz]
        
        return [
            # 1. Approach
            SimpleCommandsAction.Goal(
                command_type="set_rgb", 
                r=255,  
                g=255, 
                b=0
            ),
            
            SimpleCommandsAction.Goal(
                command_type="move",
                coords=approach_coords,
                speed=100
            ),
            
            # 2. Descend to place
            SimpleCommandsAction.Goal(
                command_type="move",
                coords=approach_coords,
                speed=100
            ),
            
            # 3. Release
            SimpleCommandsAction.Goal(command_type="vacuum_off"),
            
            # 4. Lift up
            SimpleCommandsAction.Goal(command_type="move", coords=approach_coords, speed=100)
        ]
  
  
  
  
#================== versi lengkapan

import enum
from abc import ABC, abstractmethod

# ==============================================================================
# === 1. ENUM DEFINITIONS ===
# ==============================================================================

class StateName(enum.Enum):
    """
    Enumeration of all concrete states in the machine.
    """
    IDLE = enum.auto()
    PLANNING = enum.auto()
    FETCHING_COMMAND = enum.auto()
    SENDING_COMMAND = enum.auto()
    WAIT_MOVE_DONE = enum.auto()
    WAIT_DONE = enum.auto()
    READY = enum.auto()
    DONE = enum.auto()
    ERROR = enum.auto()
    CANCELLED = enum.auto()


class Event(enum.Enum):
    """
    Enumeration of all events (transitions) that can occur.
    """
    # Transitions from IDLE
    PROCESS_WORKSPACE_BUTTON_PRESSED = enum.auto()
    PLAYBACK_BUTTON_REQUESTED = enum.auto()
    
    # Transitions within BUSY > PLANNING
    QUEUE_BUILT = enum.auto()
    
    # Transitions within BUSY > EXECUTING
    EMPTY_QUEUE_VERIFIED = enum.auto()
    COMMAND_ACQUIRED = enum.auto()
     = enum.auto()
     = enum.auto()
     = enum.auto()
     = enum.auto()
     = enum.auto()

    # Shared transitions (from BUSY superstate)
    
    # Transitions from terminal states
     = enum.auto()
     = enum.auto()


# ==============================================================================
# === 2. CONTEXT CLASS (THE MAIN MACHINE) ===
# ==============================================================================

class PlannerHSM:
    """
    The main context class that holds and manages the current state.
    
    This class holds an instance of every state and delegates event handling
    to the current state.
    """
    
    def __init__(self):
        print("PlannerHSM initializing...")
        
        # Create instances of all states, passing this context object
        self.states = {
            StateName.IDLE: IdleState(self),
            StateName.PLANNING: PlanningState(self),
            StateName.FETCHING_COMMAND: FetchingCommandState(self),
            StateName.SENDING_COMMAND: SendingCommandState(self),
            StateName.WAIT_MOVE_DONE: WaitMoveDoneState(self),
            StateName.WAIT_DONE: WaitDoneState(self),
            StateName.READY: ReadyState(self),
            StateName.DONE: DoneState(self),
            StateName.ERROR: ErrorState(self),
            StateName.CANCELLED: CancelledState(self),
        }
        
        # Set the initial state
        self.current_state = self.states[StateName.IDLE]
        self.current_state.enter()

    def transition_to(self, new_state_name: StateName):
        """
        Performs a state transition.
        """
        print(f"Transitioning from {self.current_state.name} to {new_state_name}")
        self.current_state.exit()
        self.current_state = self.states[new_state_name]
        self.current_state.enter()

    def handle_event(self, event: Event):
        """
        Passes an event to the current state for handling.
        """
        print(f"Handling event {event.name} in state {self.current_state.name}")
        self.current_state.handle_event(event)
        
    def get_current_state(self) -> StateName:
        """
        Returns the name of the current state.
        """
        return self.current_state.name

# ==============================================================================
# === 3. ABSTRACT BASE STATE ===
# ==============================================================================

class State(ABC):
    """
    Abstract base class for all concrete state implementations.
    """
    
    def __init__(self, context: PlannerHSM, name: StateName):
        self.context = context
        self.name = name

    def enter(self):
        """
        Action to perform upon entering this state.
        """
        print(f"Entering state: {self.name.name}")
        # --- ADD YOUR 'ENTRY' LOGIC HERE ---
        pass

    def exit(self):
        """
        Action to perform upon exiting this state.
        """
        print(f"Exiting state: {self.name.name}")
        # --- ADD YOUR 'EXIT' LOGIC HERE ---
        pass

    @abstractmethod
    def handle_event(self, event: Event):
        """
        Handles an incoming event. This is where transition logic lives.
        """
        pass

# ==============================================================================
# === 4. CONCRETE STATE CLASSES ===
# ==============================================================================

# --- Top-level States ---

class IdleState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.IDLE)
        
    def handle_event(self, event: Event):
        if event == Event.PROCESS_WORKSPACE_BUTTON_PRESSED:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.PLANNING)
        elif event == Event.PLAYBACK_BUTTON_REQUESTED:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.PLANNING)
        else:
            print(f"Event {event.name} unhandled in {self.name.name}")

class DoneState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.DONE)
        
    def handle_event(self, event: Event):
        if event == Event.DONE_REPORTED:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.IDLE)
        else:
            print(f"Event {event.name} unhandled in {self.name.name}")

class ErrorState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.ERROR)
        
    def handle_event(self, event: Event):
        if event == Event.ERROR_REPORTED:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.IDLE)
        else:
            print(f"Event {event.name} unhandled in {self.name.name}")

class CancelledState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.CANCELLED)

    def enter(self):
        super().enter()
        # Per the diagram, CANCELLED automatically goes back to IDLE
        # You could also wait for an event like 'CANCEL_ACKNOWLEDGED'
        print("Cancelling... returning to IDLE.")
        self.context.transition_to(StateName.IDLE)

    def handle_event(self, event: Event):
        # This state transitions automatically, so it might not handle events
        print(f"Event {event.name} unhandled in {self.name.name}")


# --- 'BUSY' Substates ---

class PlanningState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.PLANNING)
        
    def handle_event(self, event: Event):
        if event == Event.QUEUE_BUILT:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.FETCHING_COMMAND)
        
        # Handle shared 'BUSY' superstate transitions
        elif event == Event.ERROR_ACQUIRED:
            self.context.transition_to(StateName.ERROR)
        elif event == Event.CANCEL_REQUESTED:
            self.context.transition_to(StateName.CANCELLED)
        else:
            print(f"Event {event.name} unhandled in {self.name.name}")


# --- 'EXECUTING' Substates ---

class FetchingCommandState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.FETCHING_COMMAND)
        
    def handle_event(self, event: Event):
        if event == Event.COMMAND_ACQUIRED:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.SENDING_COMMAND)
        elif event == Event.EMPTY_QUEUE_VERIFIED:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.DONE)
            
        # Handle shared 'BUSY' superstate transitions
        elif event == Event.ERROR_ACQUIRED:
            self.context.transition_to(StateName.ERROR)
        elif event == Event.CANCEL_REQUESTED:
            self.context.transition_to(StateName.CANCELLED)
        else:
            print(f"Event {event.name} unhandled in {self.name.name}")

class SendingCommandState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.SENDING_COMMAND)
        
    def handle_event(self, event: Event):
        if event == Event.MOVECOMMAND_SENT:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.WAIT_MOVE_DONE)
        elif event == Event.NONMOVECOMMAND_SENT:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.WAIT_DONE)
            
        # Handle shared 'BUSY' superstate transitions
        elif event == Event.ERROR_ACQUIRED:
            self.context.transition_to(StateName.ERROR)
        elif event == Event.CANCEL_REQUESTED:
            self.context.transition_to(StateName.CANCELLED)
        else:
            print(f"Event {event.name} unhandled in {self.name.name}")

class WaitMoveDoneState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.WAIT_MOVE_DONE)
        
    def handle_event(self, event: Event):
        if event == Event.TARGET_REACHED:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.READY)

        # Handle shared 'BUSY' superstate transitions
        elif event == Event.ERROR_ACQUIRED:
            self.context.transition_to(StateName.ERROR)
        elif event == Event.CANCEL_REQUESTED:
            self.context.transition_to(StateName.CANCELLED)
        else:
            print(f"Event {event.name} unhandled in {self.name.name}")

class WaitDoneState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.WAIT_DONE)
        
    def handle_event(self, event: Event):
        if event == Event.TIMER_FINISHED:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.READY)
            
        # Handle shared 'BUSY' superstate transitions
        elif event == Event.ERROR_ACQUIRED:
            self.context.transition_to(StateName.ERROR)
        elif event == Event.CANCEL_REQUESTED:
            self.context.transition_to(StateName.CANCELLED)
        else:
            print(f"Event {event.name} unhandled in {self.name.name}")

class ReadyState(State):
    def __init__(self, context: PlannerHSM):
        super().__init__(context, StateName.READY)
        
    def handle_event(self, event: Event):
        if event == Event.NEXT_COMMAND_ASKED:
            # --- ADD LOGIC FOR THIS TRANSITION ---
            self.context.transition_to(StateName.FETCHING_COMMAND)
            
        # Handle shared 'BUSY' superstate transitions
        elif event == Event.ERROR_ACQUIRED:
            self.context.transition_to(StateName.ERROR)
        elif event == Event.CANCEL_REQUESTED:
            self.context.transition_to(StateName.CANCELLED)
        else:
            print(f"Event {event.name} unhandled in {self.name.name}")


# ==============================================================================
# === 5. EXAMPLE USAGE ===
# ==============================================================================

if __name__ == "__main__":
    # 1. Initialize the State Machine
    hsm = PlannerHSM()
    print(f"Initial state: {hsm.get_current_state()}")
    
    print("-" * 20)

    # 2. Send a sequence of events to test the logic
    
    # --- Path 1: Successful run ---
    hsm.handle_event(Event.PROCESS_WORKSPACE_BUTTON_PRESSED) # IDLE -> PLANNING
    print(f"Current state: {hsm.get_current_state()}")
    
    hsm.handle_event(Event.QUEUE_BUILT) # PLANNING -> FETCHING_COMMAND
    print(f"Current state: {hsm.get_current_state()}")

    hsm.handle_event(Event.COMMAND_ACQUIRED) # FETCHING_COMMAND -> SENDING_COMMAND
    print(f"Current state: {hsm.get_current_state()}")
    
    hsm.handle_event(Event.MOVECOMMAND_SENT) # SENDING_COMMAND -> WAIT_MOVE_DONE
    print(f"Current state: {hsm.get_current_state()}")
    
    hsm.handle_event(Event.TARGET_REACHED) # WAIT_MOVE_DONE -> READY
    print(f"Current state: {hsm.get_current_state()}")

    hsm.handle_event(Event.NEXT_COMMAND_ASKED) # READY -> FETCHING_COMMAND
    print(f"Current state: {hsm.get_current_state()}")
    
    # ... (imagine more commands) ...
    
    # Now the queue is empty
    hsm.handle_event(Event.EMPTY_QUEUE_VERIFIED) # FETCHING_COMMAND -> DONE
    print(f"Current state: {hsm.get_current_state()}")
    
    hsm.handle_event(Event.DONE_REPORTED) # DONE -> IDLE
    print(f"Current state: {hsm.get_current_state()}")
    
    print("-" * 20)

    # --- Path 2: Error handling ---
    hsm.handle_event(Event.PROCESS_WORKSPACE_BUTTON_PRESSED) # IDLE -> PLANNING
    print(f"Current state: {hsm.get_current_state()}")

    # An error occurs during planning
    hsm.handle_event(Event.ERROR_ACQUIRED) # PLANNING -> ERROR
    print(f"Current state: {hsm.get_current_state()}")

    hsm.handle_event(Event.ERROR_REPORTED) # ERROR -> IDLE
    print(f"Current state: {hsm.get_current_state()}")            
