# Code block 0
import numpy as np

# Open the gripper before approaching
open_gripper()

# Get red cube info and a grasp pose
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Approach and grasp the red cube
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube to a safe height
lift_pos = np.array(grasp_pos, dtype=float).copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

# Get green cube info
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Compute placement height (center of red cube on top of green cube)
place_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0

# Account for offset between grasp point and red cube center
grasp_offset_z = grasp_pos[2] - red_pos[2]
place_pos = np.array([green_pos[0], green_pos[1], place_z + grasp_offset_z], dtype=float)

# Move laterally above the green cube at a safe height
above_place = place_pos.copy()
above_place[2] = max(lift_pos[2], place_pos[2] + 0.1)
goto_pose(above_place, grasp_quat)

# Controlled descent to placement pose
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube
open_gripper()

# Retreat upward
retreat_pos = place_pos.copy()
retreat_pos[2] += 0.1
goto_pose(retreat_pos, grasp_quat)