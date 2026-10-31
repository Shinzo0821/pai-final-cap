# Code block 0
import numpy as np

# Get cube poses and extents
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Approach and grasp the red cube
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Compute placement height: green top + half red height, keep grasp offset relative to cube center
grasp_offset_z = grasp_pos[2] - red_pos[2]
place_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0 + grasp_offset_z
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move above the green cube and descend gently to the exact placement height
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube
open_gripper()

# Retreat upward
retreat_pos = place_pos.copy()
retreat_pos[2] += 0.1
goto_pose(retreat_pos, grasp_quat)