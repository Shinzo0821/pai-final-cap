# Code block 0
import numpy as np

red_center, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_center, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
grasp_position, grasp_quaternion = sample_grasp_pose("red cube")

open_gripper()
goto_pose(grasp_position, grasp_quaternion, z_approach=0.1)
close_gripper()

lift_position = np.array(grasp_position, dtype=float)
lift_position[2] += 0.2
goto_pose(lift_position, grasp_quaternion)

place_center = np.array(green_center, dtype=float)
place_center[2] = green_center[2] + green_extent[2] / 2 + red_extent[2] / 2
place_position = place_center + (np.asarray(grasp_position) - np.asarray(red_center))

goto_pose(place_position, grasp_quaternion, z_approach=0.1)
open_gripper()