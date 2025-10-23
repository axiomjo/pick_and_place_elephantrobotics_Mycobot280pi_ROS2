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
    IDLE = auto()
    PROCESSING = auto()
    CANCELLING = auto()
    ERROR = auto()
    DONE = auto() 
    
class PlannerHSM:
    def __init__(self,node):
        """
        initializes the HSM. node id the ros2 planner node that will be injected here.
        """
        self.node = node
        
        self.state = State.IDLE 
        self.current_goal_handle = None
        self.current_processing_task = None
        
    def is_busy(self):
        """Check if the HSM is available for a new goal."""
        return self.state != State.IDLE
        
    async def handle_new_goal(self, goal_handle):
        """ method for processing complex goal handle """
        self.node.get_logger().info("HSM: Received new complex goal.")
        
        if self.is_busy():
            # This shouldn't happen if the node's goal_callback is correct
            self.node.get_logger().warn("HSM: Was busy, goal should have been rejected.")
            return
        
        self.state = State.PROCESSING
        self.current_goal_handle = goal_handle
        self.current_processing_task = asyncio.create_task(
            self._processing_loop(goal_handle)
        )
        final_result = await self.current_processing_task
        return final_result
     
     
        
    async def handle_cancel_request(self):
        """ method for cancelled complex goal handle """
        self.node.get_logger().info("HSM: Received CANCELATION req for complex goal.")
        
        if self.state != State.PROCESSING or not self.current_processing_task:
            self.node.get_logger().warn("HSM: No active task to cancel.")
            return
        
        self.state = State.CANCELLING
        self.current_processing_task.cancel()
        
        await self.node.cancel_current_simple_command()
    
    
    
    async def _processing_loop(self, goal_handle):
        """ method for breaking down complex command to command primitives"""
        feedback = ProcessWorkspace.Feedback()
        
        try:
            objects = goal_handle.request.objects_to_move.objects
            targets = goal_handle.request.objects_target_position.points
            orientations = goal_handle.request.objects_target_orientation
            
            feedback.current_state = "Initializing to Home"
            goal_handle.publish_feedback(feedback)
            
            home_goal = SimpleCommandsAction.Goal(
                command_type="move_joints", joint_angles=[0.0] * 6, speed=100
            )
            await self.node.execute_simple_command(home_goal)
            
            for i, (obj, target, orient) in enumerate(zip(objects, targets, orientations)):
            
                if self.state == State.CANCELLING:
                    raise asyncio.CancelledError()
                
                self.node.get_logger().info(f"--- Processing Object {i+1} ---")
                feedback.current_state = f"Object {i+1}: Approaching pick pose"
                feedback.current_object = obj
                goal_handle.publish_feedback(feedback)
                
                rgb_yellow_goal = SimpleCommandsAction.Goal(command_type="set_rgb", r=255, g=255, b=0)
                await self.node.execute_simple_command(rgb_yellow_goal)
                
                RX_DOWN = 180.0
                RY_DOWN = 0.0
                
                approach_goal = SimpleCommandsAction.Goal(
                    command_type="move_blockingmode",
                    coords=[obj.center_point.x, obj.center_point.y, 70.0, RX_DOWN, RY_DOWN, 0.0],
                    speed=100
                )
                await self.node.execute_simple_command(approach_goal)
                
                feedback.current_state = f"Object {i+1}: Descending and picking"
                goal_handle.publish_feedback(feedback)
                
                rgb_red_goal = SimpleCommandsAction.Goal(command_type="set_rgb", r=255, g=0, b=0)
                await self.node.execute_simple_command(rgb_red_goal)
                
                v_strong_goal = SimpleCommandsAction.Goal(command_type="vacuum_strong")
                await self.node.execute_simple_command(v_strong_goal)
                
                descend_goal = SimpleCommandsAction.Goal(
                    command_type="move_blockingmode",
                    coords=[obj.center_point.x, obj.center_point.y, 30.0, RX_DOWN, RY_DOWN, 0.0],
                    speed=50
                )
                await self.node.execute_simple_command(descend_goal)
                
                feedback.current_state = f"Object {i+1}: Ascending to clearance"
                goal_handle.publish_feedback(feedback)
                await self.node.execute_simple_command(home_goal)
                
                feedback.current_state = f"Object {i+1}: Moving to place pose"
                goal_handle.publish_feedback(feedback)
                
                rgb_green_goal = SimpleCommandsAction.Goal(command_type="set_rgb", r=0, g=255, b=0)
                await self.node.execute_simple_command(rgb_green_goal)
                
                approach_place_goal = SimpleCommandsAction.Goal(
                    command_type="move_blockingmode",
                    coords=[target.x, target.y, 70.0, RX_DOWN, RY_DOWN, float(orient)],
                    speed=100
                )
                await self.node.execute_simple_command(approach_place_goal)
                
                feedback.current_state = f"Object {i+1}: Descending and placing"
                goal_handle.publish_feedback(feedback)
                
                descend_place_goal = SimpleCommandsAction.Goal(
                    command_type="move_blockingmode",
                    coords=[target.x, target.y, 30.0, RX_DOWN, RY_DOWN, float(orient)],
                    speed=50
                )
                await self.node.execute_simple_command(descend_place_goal)
                
                v_off_goal = SimpleCommandsAction.Goal(command_type="vacuum_off")
                await self.node.execute_simple_command(v_off_goal)
                
                lift_up_goal = SimpleCommandsAction.Goal(
                    command_type="move_blockingmode",
                    coords=[target.x, target.y, 70.0, RX_DOWN, RY_DOWN, float(orient)],
                    speed=100
                )
                await self.node.execute_simple_command(lift_up_goal)
                
            self.node.get_logger().info("All objects processed successfully.")
            self.state = State.DONE
            goal_handle.succeed()
            
            result = ProcessWorkspace.Result()
            result.success = True
            result.message = "All objects moved."
            return result
            
        except asyncio.CancelledError:
            self.node.get_logger().warn("Processing loop was CANCELLED.")
            feedback.current_state = "Cancelling and returning home"
            goal_handle.publish_feedback(feedback)
            
            home_goal = SimpleCommandsAction.Goal(
                command_type="move_joints", joint_angles=[0.0] * 6, speed=100
            )
            await self.node.execute_simple_command(home_goal)
            
            goal_handle.canceled()
            self.state = State.DONE
            
            result = ProcessWorkspace.Result()
            result.success = False
            result.message = "Process cancelled by user."
            return result
            
        except Exception as e:
            self.node.get_logger().error(f"HSM Error: {str(e)}")
            self.state = State.ERROR
            goal_handle.abort()
            
            result = ProcessWorkspace.Result()
            result.success = False
            result.message = f"Error: {str(e)}"
            return result
            
        finally:
            self.node.get_logger().info("HSM returning to IDLE.")
            self.state = State.IDLE
            self.current_goal_handle = None
            self.current_processing_task = None
            
            
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
        
