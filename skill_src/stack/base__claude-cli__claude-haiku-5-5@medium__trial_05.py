# Code block 0
import numpy as np

# Locate both cubes
red_pos, red_quat, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube and reuse its quaternion for placement
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper before approaching
open_gripper()

# Approach and descend to grasp pose with controlled z_approach
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Grasp the cube
close_gripper()

# Lift to a safe height (at least +0.2m) before lateral motion
safe_height = 0.2
lift_pos = np.array([grasp_pos[0], grasp_pos[1], grasp_pos[2] + safe_height])
goto_pose(lift_pos, grasp_quat)

# Compute placement position on top of the green cube
red_half_h = red_extent[2] / 2.0
green_half_h = green_extent[2] / 2.0
place_z = green_pos[2] + green_half_h + red_half_h
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move laterally above the green cube at safe height
above_place = np.array([place_pos[0], place_pos[1], place_pos[2] + safe_height])
goto_pose(above_place, grasp_quat)

# Descend onto the green cube with controlled approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube
open_gripper()

# Retreat upward to a safe height after release
retreat_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + safe_height])
goto_pose(retreat_pos, grasp_quat)