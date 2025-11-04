"""
#prn_hsm_states.py

the Hierarchical State Machine state implementation. 
it just knows what states exists and what to do in each states.
also takes care of planning logic uses asyncio await
"""

import asyncio
from enum import Enum, auto
from mycobot280pi_interfaces.action import ProcessWorkspace, SimpleCommandsAction

# state is the fsm circles
class StateName(Enum):
    
    # top-level states
    IDLE = auto()
    BUSY = auto()
    DONE = auto() 
    ERROR = auto()
    CANCELLED = auto()
    
    # BUSY superstate's states
    busy_PLANNING = auto()
    busy_FETCHING_COMMAND = auto()
    busy_SENDING_COMMAND = auto()
    busy_WAITING_MOVE_DONE = auto()
    busy_WAITING_DONE = auto() 
    busy_READY = auto() 
    
    """
    # not implemented krn waktu gacukup
    busy_RECORDING = auto()
    

    # BUSY RECORDING's state
    busy_recording_START = auto()
    busy_recording_RECORDING = auto()
    busy_recording_END = auto()
    busy_recording_SAVE = auto() 
    busy_recording_DELETE = auto()
    """

# event is fsm arrow labels      
class Event(Enum):        
    
    # --- from IDLE ---
    PROCESS_WORKSPACE_BUTTON_PRESSED = auto()        
    
    # --- from BUSY ---
    ERROR_ACQUIRED = auto()
    CANCEL_REQUESTED = auto()
    
    # ------- from busy_PLANNING ------
    QUEUE_BUILT = auto()
    # ------- from busy_FETCHING_COMMAND ------
    EMPTY_QUEUE_VERIFIED = auto() 
    COMMAND_ACQUIRED = auto()   
    # ------- from busy_SENDING_COMMAND ------
    MOVECOMMAND_SENT = auto()
    NONMOVECOMMAND_SENT = auto()
    # ------- from busy_WAITING_MOVE_DONE ------
    TARGET_REACHED = auto() 
    # ------- from busy_WAITING_DONE ---
    TIMER_FINISHED = auto()
    # ------- from busy_READY ------
    NEXT_COMMAND_ASKED = auto() 
    
    # --- from DONE ---
    DONE_REPORTED = auto()        
    
    # --- from ERROR ---
    ERROR_REPORTED = auto()        
    
    # --- from CANCELLED ---
    CANCEL_REPORTED = auto()        
    

     
#====== jojo baru ngupdate sampe sini


class PlannerHSM:
    def __init__(self,node):
        """
        The 'Context' class that manages the states.
        initializes the HSM. 
        node is the ros2 planner node that will be injected here.
        """
        self.node = node
        
        # --- FSM State ---
        self.current_state = None
       
        # --- ROS Action Properties ---
        self.current_goal_handle = None
        
        # --- The "Conveyor Belt" ---
        self.plan_queue = []
        self.current_command = None
        
        # --- Async Synchronization to signal finished task ---
        self.task_complete_event = None
        self.final_result = None # Stores the action result
        
        # --- closed loop feedback ---
        self.target_coords = None
        
        # --- Start the machine asyncly ---
        self.current_state = IdleState()
        self.current_state.enter_sync(self)

    async def transition_to(self, new_state):
        """
        Handles the async transition between states.
        """
        if self.current_state:
            await self.current_state.exit(self)
    
        self.current_state = new_state
        await self.current_state.enter(self)
        
        
    async def handle_event(self, event: EventID, data=None):
        """
        The main internal async event handler.
        """
        self.node.get_logger().info(f"[HSM Event: {event.name}]")
        new_state = await self.current_state.handle_event(self, event, data
        
        if new_state:
            await self.transition_to(new_state)
            
    def get_current_state_id(self):
        """Gets the enum ID of the most specific current state."""
        return self.current_state.get_id()
        
    # --- Public API called by PlannerNode ---
    def is_busy(self):
        """
        Called by goal_callback to check if the HSM is available.
        """
        current_id = self.get_current_state_id()
        
        is_resting = current_id in [
            StateID.IDLE, 
            StateID.DONE, 
            StateID.CANCELLED, 
            StateID.ERROR
        ]
        
        return not is_resting
        
    async def handle_new_goal(self, goal_handle):
        """
        This is the main long-running task for the action server.
        It will only return when the task is done, cancelled, or errors.
        """
        self.node.get_logger().info("HSM received new goal.")
        self.current_goal_handle = goal_handle
        self.final_result = None
        self.task_complete_event = asyncio.Event()
        
        # (This will transition from IDLE to BUSY -> busy_PLANNING)
        await self.handle_event(EventID.NEW_GOAL, goal_handle)
        
        await self.task_complete_event.wait()
        
        self.node.get_logger().info("HSM task finished. Returning result.")
        return self.final_result
        
        
    async def handle_cancel_request(self):
        """
        Called by the node's cancel_callback.
        """
        self.node.get_logger().warn("HSM processing CANCEL request.")
        await self.handle_event(EventID.CANCEL)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
class State:
    """
    The base class 'interface' for all States.
    async.
    """
    
    def get_id(self):
        """Returns the StateID enum for this state."""
        # This forces all child classes to implement this method
        raise NotImplementedError
        
    async def enter(self, hsm: PlannerHSM): 
        """Called when this state is entered."""
        # We can now use the ROS node for logging!
        hsm.node.get_logger().info(f"Entering: {self.get_id().name}")
        pass
        
    async def exit(self, hsm: PlannerHSM):
        """Called when this state is exited."""
        hsm.node.get_logger().info(f"Exiting: {self.get_id().name}")
        pass
        
    def handle_event(self, robot, event, data=None):
        """
        Called to handle an event.
        Must return a new State object if a transition is needed,
        otherwise return None.
        
        'data' is an optional argument for passing payloads
        (e.g., 'PICK_N_PLACE', {'x': 100, 'y': 50})
        """
        return None
   
# the top-level state classes
"""
    IDLE = auto()
    BUSY = auto()
    CANCELLED = auto()
    ERROR = auto()
    DONE = auto() 
"""
class DoneState(State):
    def get_id(self):
        return StateID.DONE
        
    async def enter(self, hsm: PlannerHSM):
        await super().enter(hsm)
        
        result = ProcessWorkspace.Result()
        result.success = True
        result.message = "Task completed successfully."
        hsm.final_result = result
        
        if hsm.current_goal_handle:
            hsm.current_goal_handle.succeed()
        
        if hsm.task_complete_event:
            hsm.task_complete_event.set()
        
class CancelledState(State):
    def get_id(self):
        return StateID.CANCELLED
        
    async def enter(self, hsm: PlannerHSM):
        await super().enter(hsm)
        
        result = ProcessWorkspace.Result()
        result.success = False
        result.message = "Task was cancelled."
        hsm.final_result = result
        
        if hsm.current_goal_handle:
            hsm.current_goal_handle.canceled()
            
        if hsm.task_complete_event:
            hsm.task_complete_event.set()

class ErrorState(State):
    def get_id(self):
        return StateID.ERROR
        
    async def enter(self, hsm: PlannerHSM):
        await super().enter(hsm)
        
        result = ProcessWorkspace.Result()
        result.success = False
        result.message = "Task failed with an error."
        hsm.final_result = result
        
        if hsm.current_goal_handle:
            hsm.current_goal_handle.abort()
            
        if hsm.task_complete_event:
            hsm.task_complete_event.set()
   
     
class BusyExecutingSendCommandState(State):
    def get_id(self):
        return StateID.busy_executing_SEND_COMMAND
        
    async def enter(self, hsm: PlannerHSM):
        await super().enter(hsm)
        
        try:
            # Assume a previous state (FETCH) set this
            command_to_run = hsm.current_command
            
            if not command_to_run:
                raise Exception("No command was fetched.")
     
            hsm.node.get_logger().info("Calling execute_simple_command...")
            await hsm.node.execute_simple_command(command_to_run)
            
            await hsm.handle_event("SEND_COMPLETE")
            
        except asyncio.CancelledError:
            hsm.node.get_logger().warn("execute_simple_command was cancelled.")
            
        except Exception as e:
            hsm.node.get_logger().error(f"Failed to execute simple command: {e}")
            await hsm.handle_event("ERROR")
             
    async def handle_event(self, hsm: PlannerHSM, event, data=None):
        if event == "SEND_COMPLETE":
            # Go to the next step in the execution engine
            return BusyExecutingWaitMoveCompleteState() # (You'd define this class)
        return None 
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
