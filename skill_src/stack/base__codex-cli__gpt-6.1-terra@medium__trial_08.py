# Code block 0
import numpy as np

red_center, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_center, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

place_z = green_center[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_center[0], green_center[1], place_z])
place_pos += np.asarray(grasp_pos) - np.asarray(red_center)

safe_z = max(grasp_pos[2] + 0.2, place_pos[2] + 0.1)
lift_pos = np.array(grasp_pos, dtype=float)
lift_pos[2] = safe_z
goto_pose(lift_pos, grasp_quat)

above_place = np.array([place_pos[0], place_pos[1], safe_z])
goto_pose(above_place, grasp_quat)
goto_pose(place_pos, grasp_quat, z_approach=0.1)
open_gripper()