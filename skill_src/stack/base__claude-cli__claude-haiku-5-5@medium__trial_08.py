# Code block 0
import numpy as np

# Locate the cubes
red_pos, _, red_ext = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_ext = get_object_pose("green cube", return_bbox_extent=True)

# Grasp pose for the red cube (quaternion from sample_grasp_pose is the one to use)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper, then approach the grasp pose with a controlled descent
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close gripper to grasp the red cube
close_gripper()

# Lift to a safe height (at least +0.2 m in Z) before lateral motion
safe_z = grasp_pos[2] + 0.2
lift_pos = np.array([grasp_pos[0], grasp_pos[1], safe_z])
goto_pose(lift_pos, grasp_quat)

# Compute placement position on top of the green cube
# place_z = green_center_z + green_extent[2]/2 + red_extent[2]/2
place_z = green_pos[2] + green_ext[2] / 2.0 + red_ext[2] / 2.0
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move laterally at safe height above the green cube
above_green = np.array([green_pos[0], green_pos[1], safe_z])
goto_pose(above_green, grasp_quat)

# Descend onto the green cube with controlled approach, reusing the grasp quaternion
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube
open_gripper()

# Retreat upward to a safe height so the gripper clears the stack
retreat_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.2])
goto_pose(retreat_pos, grasp_quat)