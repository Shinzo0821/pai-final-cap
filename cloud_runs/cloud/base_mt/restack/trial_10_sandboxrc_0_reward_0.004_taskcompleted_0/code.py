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

# Lift the red cube straight up to clear the environment
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Compute placement: red cube bottom should sit on green cube top.
# The gripper holds the red cube at grasp height; offset of gripper relative to red cube center:
grasp_offset_z = grasp_pos[2] - red_pos[2]
# Target red cube center z when resting on green cube
target_red_center_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
place_pos = np.array([green_pos[0], green_pos[1], target_red_center_z + grasp_offset_z])

# Move above the green cube, then descend gently to the placement height
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube gently and retreat
open_gripper()
retreat_pos = place_pos.copy()
retreat_pos[2] += 0.1
goto_pose(retreat_pos, grasp_quat)