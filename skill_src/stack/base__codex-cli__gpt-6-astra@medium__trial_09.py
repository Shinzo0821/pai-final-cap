# Code block 0
import numpy as np

red_center, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_center, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
grasp_position, grasp_quaternion = sample_grasp_pose("red cube")

open_gripper()
goto_pose(grasp_position, grasp_quaternion, z_approach=0.1)
close_gripper()

place_z = green_center[2] + green_extent[2] / 2 + red_extent[2] / 2
place_position = np.array([green_center[0], green_center[1], place_z])
place_grasp_position = place_position + (grasp_position - red_center)

safe_position = np.array(grasp_position, copy=True)
safe_position[2] = max(grasp_position[2] + 0.2, place_grasp_position[2] + 0.1)
goto_pose(safe_position, grasp_quaternion)

above_place = np.array(place_grasp_position, copy=True)
above_place[2] = safe_position[2]
goto_pose(above_place, grasp_quaternion)
goto_pose(place_grasp_position, grasp_quaternion, z_approach=0.1)
open_gripper()