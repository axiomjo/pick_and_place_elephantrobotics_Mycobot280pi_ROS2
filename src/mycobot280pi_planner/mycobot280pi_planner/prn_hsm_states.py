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
    
    # BUSY's sub states
    busy_PLANNING = auto()
    busy_EXECUTING = auto()
    
    # sub sub states
    busy_executing_FETCHING_COMMAND = auto()
    busy_executing_SENDING_COMMAND = auto()
    busy_executing_WAITING_MOVE_DONE = auto()
    busy_executing_WAITING_DONE = auto() 
    busy_executing_READY = auto() 
    
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
    
    # ------- from busy_executing_FETCHING_COMMAND ------
    QUEUE_EMPTIED = auto() 
    COMMAND_ACQUIRED = auto()   
    # ------- from busy_executing_SENDING_COMMAND ------
    MOVECOMMAND_SENT = auto()
    NONMOVECOMMAND_SENT = auto()
    # ------- from busy_executing_WAITING_MOVE_DONE ------
    TARGET_REACHED = auto() 
    # ------- from busy_executing_WAITING_DONE ---
    TIMER_FINISHED = auto()
    # ------- from busy_executing_READY ------
    NEXT_COMMAND_ASKED = auto() 
    
    # --- from DONE ---
    DONE_REPORTED = auto()        
    
    # --- from ERROR ---
    ERROR_REPORTED = auto()        
    
    # --- from CANCELLED ---
    CANCEL_REPORTED = auto()        
    

     


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
        self.node.get_logger().info("HSM starting in IDLE.")
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
        
        
    async def handle_event(self, event: Event, data=None):
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
            StateName.IDLE, 
            StateName.DONE, 
            StateName.CANCELLED, 
            StateName.ERROR
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
        await self.handle_event(Event.NEW_GOAL, goal_handle)
        
        await self.task_complete_event.wait()
        
        self.node.get_logger().info("HSM task finished. Returning result.")
        return self.final_result
        
        
    async def handle_cancel_request(self):
        """
        Called by the node's cancel_callback.
        """
        self.node.get_logger().warn("HSM processing CANCEL request.")
        await self.handle_event(Event.CANCEL)
              
              
              
              
              
        
        
     
        
class State:
    """
    The base class 'interface' for all States.
    async.
    """
    
    def get_id(self):
        """Returns the StateName enum for this state."""
        # This forces all child classes to implement this method
        raise NotImplementedError
        
    def enter_sync(self, hsm: 'PlannerHSM'):
        """A special non-async enter for the __init__ method."""
        hsm.node.get_logger().info(f"Entering: {self.get_id().name}")
    
    async def enter(self, hsm: PlannerHSM): 
        """Called when this state is entered."""
        # We can now use the ROS node for logging!
        hsm.node.get_logger().info(f"Entering: {self.get_id().name}")
        pass
        
    async def exit(self, hsm: PlannerHSM):
        """Called when this state is exited."""
        hsm.node.get_logger().info(f"Exiting: {self.get_id().name}")
        pass
        
    async def handle_event(self, hsm: PlannerHSM, event, data=None):
        """
        Called to handle an event.
        Must return a new State object if a transition is needed,
        otherwise return None.
        
        'data' is an optional argument for passing payloads
        (e.g., 'PICK_N_PLACE', {'x': 100, 'y': 50})
        """
        return None
   





"""
ALL LEVEL-1 states.

    IDLE = auto()
    BUSY = auto()
    DONE = auto() 
    ERROR = auto()
    CANCELLED = auto()
"""
class IdleState(State):
    def get_id(self):
        return StateName.DONE
        
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
        

class BusyState(State):
    def __init__(self, initial_substate_id: StateName):
        """
        When this state is created, it immediately creates
        its starting child state ("Team Lead").
        """
        self.current_substate = None
        
        if initial_substate_id == StateID.busy_PLANNING:
            self.current_substate = BusyPlanningState()
        elif initial_substate_id == StateID.busy_EXECUTING:
            self.current_substate = BusyExecutingState()
        else:
            self.current_substate = BusyPlanningState()
            
    def get_id(self):
        return StateName.busy_executing_SEND_COMMAND
        
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


class DoneState(State):
    def get_id(self):
        return StateName.DONE
        
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
        return StateName.CANCELLED
        
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
        return StateName.ERROR
        
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
   
       
     
     
     
     
class FetchCommandState(State):
    """
    This "Worker" state's job is to check the plan_queue
    and decide what to do next.
    """
    def get_id(self): 
        return StateID.busy_executing_FETCH_COMMAND
    
    async def enter(self, hsm: PlannerHSM):
        await super().enter(hsm)
        
        if len(hsm.plan_queue) > 0:
            # 1. Work: Get the next command
            hsm.current_command = hsm.plan_queue.pop(0) 
            hsm.node.get_logger().info(f"Fetched command: {hsm.current_command.command_type}")
            
            # 2. Fire event to go to the NEXT worker
            await hsm.handle_event(EventID.command_acquired)
        else:
            # 3. Work is done! Queue is empty.
            hsm.node.get_logger().info("Plan queue empty. Execution complete.")
            
            # 4. Fire the "escape" event to go to DONE
            await hsm.handle_event(EventID.queue_emptied)
            
    async def handle_event(self, hsm, event, data):
        # This state is "completionist" for its two events
        
        if event == EventID.command_acquired:
            # This transitions to its sibling
            return BusyExecutingSendCommandState() 
            
        if event == EventID.queue_emptied:
            # This "escapes" to the top-level
            return DoneState() 
            
        return None # Ignore other events     
     
     
     
     
     
     
     
     
     
     
     
     
     
