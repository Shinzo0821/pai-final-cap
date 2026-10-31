# Code block 0
import numpy as np

# Open gripper prior to grasping
open_gripper()

# Get poses and bounding box extents for both cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Approach and grasp the red cube
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the cube to a safe height (at least +0.2m in Z) before moving laterally
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

# Calculate placement position on top of the green cube
place_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move to the placement position with controlled descent using z_approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube
open_gripper()