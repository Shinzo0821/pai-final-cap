# Code block 0
import numpy as np

# Perceive red and green cubes
red_pos, red_quat, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Grasp pose for red cube (use sampled grasp quaternion)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper and approach red cube with controlled descent
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift to safe height (at least +0.2 m in Z) before lateral motion
lift_pos = np.array([grasp_pos[0], grasp_pos[1], grasp_pos[2] + 0.2])
goto_pose(lift_pos, grasp_quat)

# Compute placement position on top of green cube
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move above placement location at safe height, then approach with z_approach
safe_above_place = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.2])
goto_pose(safe_above_place, grasp_quat)
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release cube gently
open_gripper()

# Retreat upward to a safe height after release
retreat_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.2])
goto_pose(retreat_pos, grasp_quat)