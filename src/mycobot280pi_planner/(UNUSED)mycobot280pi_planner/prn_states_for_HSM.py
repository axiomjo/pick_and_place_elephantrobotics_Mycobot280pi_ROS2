"""
 prn_states_for_HSM.py file contains every states that is used in the design of this HSM.
 
 each state has its own class. and every state will inherit the BaseState class so i dont need to rewrite the basic functionalities over and over again
"""
import asyncio
from rclpy.node import Node

class BaseState:
    def __init__(self, name):
        self.name = name
    
    # Must be 'async def' because it will await Action results
    async def execute(self, user_data: dict, clients: dict):
        """
        Runs the state logic and returns the outcome string.
        :param user_data: The shared data dictionary.
        :param clients: Dictionary of injected Action Client helpers.
        """
        # Placeholder logic: just print and succeed
        print(f"Executing State: {self.name}")
        return 'succeeded' # Possible outcomes: 'succeeded', 'aborted', 'preempted'
    
    def exit(self):
        print(f"Exiting State: {self.name}")
        
class Initialize(BaseState):
    """
    State to initialize the robot, usually moving to a home/safe pose.
    """
    def __init__(self):
        super().__init__('INITIALIZE')
    
    async def execute(self, user_data: dict, clients: dict):
        node = user_data['node'] # Access the Planner node for logging
        
        # 1. Get the MoveArm client instance
        move_client = clients.get('move_arm_client')
        if not move_client:
            node.get_logger().error("Initialize state failed: MoveArm client not available.")
            return 'aborted'
            
        node.get_logger().info("INITIALIZE: Sending MoveToHome pose...")
        
        # 2. Define the home pose
        home_pose = [0.0] * 6 # Replace with actual MyCobot home pose
        
        # 3. Non-blocking call to the Action Client helper
        # This is where the function will pause and yield control
        outcome = await move_client.send_goal_and_wait(home_pose)
        
        if outcome == 'succeeded':
            node.get_logger().info("INITIALIZE: MoveToHome succeeded. System Ready.")
        else:
            node.get_logger().error("INITIALIZE: MoveToHome failed.")
            
        return outcome # Will be 'succeeded' or 'aborted'
        
        
        
class ApproachPickPose(BaseState):
    def __init__(self):
        super().__init__('APPROACH_PICK_POSE')
    
    async def execute(self, user_data: dict, clients: dict):
        # 1. Get client and data (pick pose was placed in user_data by a VISION state)
        node = user_data['node']
        primitive_client = clients.get('primitive_client')
        
        # NOTE: You will need a VISION state before this to populate 'pick_data'
        obj_data = user_data.get('current_object_data') 
        
        # 2. Define the goal (Move Above Object)
        goal_coords = [obj_data.x, obj_data.y, 70.0, RX_DOWN, RY_DOWN, 0.0]
        
        # 3. Execute the command (Step 3 in your old logic)
        outcome = await primitive_client.send_command_and_wait(
            command_type="move_blockingmode",
            coords=goal_coords,
            speed=100
        )
        return outcome
