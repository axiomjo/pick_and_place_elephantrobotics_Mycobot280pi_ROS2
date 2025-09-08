# Interface type: mycobot280pi_interfaces/msg/OneDetectedObject
# Filepath: src/mycobot280pi_interfaces/msg/OneDetectedObject.msg
# Uses: Point2D (as center_point)
# Used in: ManyDetectedObjects (as objects[]), ProcessWorkspace.action (as objects_to_move[])
#OneDetectedObject.msg

int32 id                 # assigned number upon detection

Point2D center_point     # bounding box center point
int32 width              # bounding box width
int32 height             # bounding box height

