"""
# prn_main.py

main entrypoint.
"""

import rclpy
import asyncio
from .prn_action_client_server import PlannerNode

async def main_async(args=None):
    """
    Main async function to run the node and spin rclpy.
    """
    rclpy.init(args=args)
    planner_node = None
    
    planner_node = PlannerNode()
    
    while rclpy.ok():
        rclpy.spin_once(planner_node, timeout_sec=0.01)
        await asyncio.sleep(0.001)
        
    if planner_node:    
        planner_node.destroy_node()
    rclpy.shutdown()
    
def main(args=None): 
    asyncio.run(main_async(args))

if __name__ == '__main__':
    main()
