# Code block 0
import numpy as np

# Get object poses and extents
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper and approach red cube
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Grasp
close_gripper()

# Lift to safe height
lift_pos = np.array(grasp_pos, dtype=float).copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

# Compute placement position
place_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
# Account for offset between grasp point and red cube center in z
grasp_offset_z = grasp_pos[2] - red_pos[2]
place_pos = np.array([green_pos[0], green_pos[1], place_z + grasp_offset_z], dtype=float)

# Move laterally above green cube at safe height
above_place = place_pos.copy()
above_place[2] = max(lift_pos[2], place_pos[2] + 0.2)
goto_pose(above_place, grasp_quat)

# Controlled descent to placement pose
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release
open_gripper()

# Retreat upward
retreat_pos = place_pos.copy()
retreat_pos[2] += 0.1
goto_pose(retreat_pos, grasp_quat)