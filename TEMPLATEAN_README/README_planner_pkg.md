
### 4. `mycobot280pi_planner` Package Contents 🤖

#### Node Contents

##### `planner_robot_node` 🤖

- **Separation of Concerns:**
  - `mycobot280pi_planner/rpn_main_ros_node.py` (The main ROS node file).
  - `mycobot280pi_planner/rpn_planning_logic.py` (The core Finite-State-Machine implementation for planning and decision-making logic).
  - `mycobot280pi_planner/rpn_action_server.py` (A class to handle the action server).
  - `mycobot280pi_planner/rpn_service_server.py` (A class to handle the service server).

Separation of Concerns
1. rpn_main_ros_node.py
The main entry point and ROS node. Handles all ROS communication and delegates logic to the other modules.

Initializes the node and all publishers/subscribers/servers/clients.
Subscribes to:
/vision/detected_objects (for auto pick-and-place)
/planner/manual_commands (for manual control from GUI)
Publishes to:
/planner/commands (atomic commands for executor)
Hosts:
/planner/set_coords (service server)
/planner/process_workspace (action server)
Delegates planning logic to rpn_planning_logic.py.
2. rpn_planning_logic.py
Contains the core finite-state-machine (FSM) and planning logic.

Receives high-level goals (from action/service/manual).
Maintains the current plan and state.
Breaks down high-level tasks (e.g., pick-and-place) into a sequence of atomic SimpleCommands.
Handles feedback and error recovery.
Calls back to rpn_main_ros_node.py to publish commands.
3. rpn_action_server.py
Implements the /planner/process_workspace action server.

Handles requests from the GUI to process the workspace (e.g., full pick-and-place cycle).
Calls into rpn_planning_logic.py to generate and execute the plan.
Sends feedback and result to the GUI.

4. rpn_service_server.py
Implements the /planner/set_coords service server.

Handles manual coordinate requests from the GUI.
Calls into rpn_planning_logic.py to execute the move and respond.



How the Planner Node Works Together
Manual Command:

GUI publishes to /planner/manual_commands (e.g., move, vacuum_on).
rpn_main_ros_node.py receives, passes to rpn_planning_logic.py, which immediately publishes the corresponding atomic command to /planner/commands.
Automated Pick-and-Place:

GUI or user triggers /planner/process_workspace action.
rpn_action_server.py receives the goal, calls rpn_planning_logic.py to generate a sequence (move to object, vacuum_on, move to drop, vacuum_off, etc.).
For each step, rpn_planning_logic.py publishes a SimpleCommands message to /planner/commands.
Waits for feedback (could be via a status topic or by waiting a fixed time).
Sends feedback/result to the GUI.
Manual Set Coords:

GUI calls /planner/set_coords service.
rpn_service_server.py receives, calls rpn_planning_logic.py to execute the move, and responds.





"""rpn_action_server.pyImplements the /planner/process_workspace action server for the planner node.Receives a list of objects to move (with their target positions/orientations) from the GUI,and coordinates the pick-and-place sequence for each object, providing feedback as it works."""import rclpyfrom rclpy.action import ActionServerfrom rclpy.node import Nodefrom mycobot280pi_interfaces.action import ProcessWorkspacefrom mycobot280pi_interfaces.msg import OneDetectedObject, ManyDetectedObjects, Point2DArrayclass PlannerActionServer:    def __init__(self, node, logic):        self.node = node        self.logic = logic        self._action_server = ActionServer(            node,            ProcessWorkspace,            '/planner/process_workspace',            self.execute_callback        )    async def execute_callback(self, goal_handle):        self.node.get_logger().info("Received process_workspace action goal.")        objects = goal_handle.request.objects_to_move.objects        target_positions = goal_handle.request.objects_target_position.points        target_orientation = goal_handle.request.objects_target_orientation        feedback_msg = ProcessWorkspace.Feedback()        result_msg = ProcessWorkspace.Result()        try:            # Check that the number of objects matches the number of target positions            if len(objects) != len(target_positions):                result_msg.success = False                result_msg.message = "Mismatch between objects and target positions."                goal_handle.abort()                return result_msg            for idx, obj in enumerate(objects):                # Assign target position and orientation to the object (if needed)                obj_target = target_positions[idx]                # Optionally, you can add orientation to obj if your message supports it                # Call planning logic to process this object                # This should break down the task and publish atomic commands                async for state in self.logic.pick_and_place_object(obj, obj_target, target_orientation):                    feedback_msg.current_state = state                    feedback_msg.current_object = obj                    goal_handle.publish_feedback(feedback_msg)                    await rclpy.sleep(0.1)  # Simulate work or wait for real feedback            result_msg.success = True            result_msg.message = "All objects processed successfully."            goal_handle.succeed()        except Exception as e:            result_msg.success = False            result_msg.message = f"Error: {e}"            goal_handle.abort()        return result_msg
How to use this:

The logic.pick_and_place_object(obj, obj_target, target_orientation) should be an async generator in your planning logic that yields the current FSM state as a string for feedback.
The action server checks that the number of objects matches the number of target positions.
For each object, it processes the pick-and-place sequence, publishing feedback as it goes.
On completion, it returns a success result.

