"""
#prn_hsm_states.py

the Hierarchical State Machine state implementation. 
it just knows what states exists and what to do in each states.
also takes care of planning logic uses asyncio await
"""

import asyncio
from enum import Enum, auto
from mycobot280pi_interfaces.action import ProcessWorkspace, SimpleCommandsAction

class State(Enum):
    #auto() is used coz the assigned number doesn't matter, as long as they're unique to each other
    IDLE = auto()
    BUSY = auto()
    CANCELLING = auto()
    ERROR = auto()
    DONE = auto() 

    # BUSY superstate's states
    busy_BUILDING_PLAN = auto()
    busy_GETTING_NEXT_COMMAND = auto()
    busy_SENDING_COMMAND = auto()
    busy_WAITING_FOR_RESULT = auto()
    busy_WAITING_FOR_MOVE_COMPLETE = auto()    
    
    
    
class PlannerHSM:
    def __init__(self,node):
        """
        initializes the HSM. node id the ros2 planner node that will be injected here.
        """
        self.node = node
        
        # --- FSM State ---
        self.state = State.IDLE 
        self.current_goal_handle = None
        
        # --- The "Conveyor Belt" ---
        self.plan_queue = []
        self.current_command = None
        
        # --- closed loop feedback ---
        self.target_angles = None
        
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
            
        
