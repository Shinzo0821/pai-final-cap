# Code block 0
import numpy as np

# Get poses and extents
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube (use its quaternion)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Approach the red cube from above and grasp it
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube to a safe height
lift_pos = np.copy(grasp_pos)
lift_pos[2] += 0.2  # +0.2 m in Z
goto_pose(lift_pos, grasp_quat)

# Compute stacking height using the given formula
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2

# Define the placement position (use green cube's XY)
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Approach the placement position from above using the same grasp orientation
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube onto the green cube
open_gripper()

# Retract to a safe height after placing
retract_pos = np.copy(place_pos)
retract_pos[2] += 0.2
goto_pose(retract_pos, grasp_quat)