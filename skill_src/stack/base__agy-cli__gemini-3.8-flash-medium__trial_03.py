# Code block 0
import numpy as np

# Open gripper prior to grasping
open_gripper()

# Sample grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Approach and grasp the red cube
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the cube to a safe height (+0.2m in Z) before moving laterally
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

# Retrieve object poses and extents for stacking calculation
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)

# Calculate placement position using the stacking height formula
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move to the placement position with controlled descent using the grasp orientation
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube
open_gripper()