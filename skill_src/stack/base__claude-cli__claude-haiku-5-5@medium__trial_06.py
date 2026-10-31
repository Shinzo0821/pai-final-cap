# Code block 0
import numpy as np

# Look up the red and green cubes
red_pos, red_quat, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Grasp pose for the red cube (reuse this quaternion for placement)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Make sure the gripper starts open
open_gripper()

# Approach the grasp pose from above with a controlled descent
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close the gripper to grasp the cube
close_gripper()

# Lift the cube to a safe height (at least +0.2 m in Z)
lift_pos = np.array([grasp_pos[0], grasp_pos[1], grasp_pos[2] + 0.2])
goto_pose(lift_pos, grasp_quat)

# Compute the placement position on top of the green cube
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move laterally at the safe height above the placement location
safe_above_place = np.array([place_pos[0], place_pos[1], lift_pos[2]])
goto_pose(safe_above_place, grasp_quat)

# Descend onto the green cube with a controlled approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube
open_gripper()

# Retreat upward to clear the stack
retreat_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.2])
goto_pose(retreat_pos, grasp_quat)