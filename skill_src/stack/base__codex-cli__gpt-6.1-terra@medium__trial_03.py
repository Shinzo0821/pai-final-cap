# Code block 0
import numpy as np

red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

lift_pos = np.array(grasp_pos, dtype=float)
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

place_center = np.array(green_pos, dtype=float)
place_center[2] = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = place_center + (np.asarray(grasp_pos) - np.asarray(red_pos))

safe_pos = np.array(place_pos, dtype=float)
safe_pos[2] = max(lift_pos[2], place_pos[2] + 0.1)
goto_pose(safe_pos, grasp_quat)
goto_pose(place_pos, grasp_quat, z_approach=0.1)
open_gripper()