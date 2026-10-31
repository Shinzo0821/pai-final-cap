# Code block 0
import numpy as np

red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

grasp_pos, grasp_quat = sample_grasp_pose("red cube")

open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

lift_pos = np.array([grasp_pos[0], grasp_pos[1], grasp_pos[2] + 0.2], dtype=float)
goto_pose(lift_pos, grasp_quat)

place_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
place_pos = np.array([green_pos[0], green_pos[1], place_z], dtype=float)
goto_pose(place_pos, grasp_quat, z_approach=0.1)
open_gripper()

retreat_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.1], dtype=float)
goto_pose(retreat_pos, grasp_quat)