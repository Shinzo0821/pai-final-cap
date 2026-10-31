# Code block 0
import numpy as np

# Get object poses and extents
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube (provides reliable orientation)
red_grasp_pos, red_grasp_quat = sample_grasp_pose("red cube")

# Open gripper and approach the red cube
open_gripper()
goto_pose(red_grasp_pos, red_grasp_quat, z_approach=0.1)

# Close gripper to grasp the red cube
close_gripper()

# Lift the cube to a safe height (+0.2 m in Z)
lift_pos = red_grasp_pos + np.array([0.0, 0.0, 0.2])
goto_pose(lift_pos, red_grasp_quat, z_approach=0.0)

# Compute the stacking placement height
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Approach the placement pose using the same grasp orientation
goto_pose(place_pos, red_grasp_quat, z_approach=0.1)

# Release the red cube onto the green cube
open_gripper()