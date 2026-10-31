# Code block 0
import numpy as np

# Open gripper to prepare for grasping
open_gripper()

# Get object poses and bounding box extents
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Approach and grasp the red cube
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube to a safe height (at least +0.2m in Z)
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

# Calculate placement position based on green cube center and half-height extents
place_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move laterally to the placement location at the safe height
lateral_pos = np.array([place_pos[0], place_pos[1], lift_pos[2]])
goto_pose(lateral_pos, grasp_quat)

# Gently place the red cube on top of the green cube with controlled descent
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube
open_gripper()