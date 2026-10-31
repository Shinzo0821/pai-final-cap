# Code block 0
import numpy as np

# Get poses and extents of both cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Approach and grasp the red cube
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Compute placement: red cube center should sit at green top + half red height
# Gripper offset relative to red cube center is preserved from grasp
grasp_offset = grasp_pos - red_pos
green_top_z = green_pos[2] + green_extent[2] / 2.0
target_red_center = np.array([green_pos[0], green_pos[1], green_top_z + red_extent[2] / 2.0])
place_pos = target_red_center + grasp_offset

# Move above the green cube then descend gently and release
goto_pose(place_pos, grasp_quat, z_approach=0.1)
open_gripper()

# Retreat upward
retreat_pos = place_pos.copy()
retreat_pos[2] += 0.1
goto_pose(retreat_pos, grasp_quat)