# Code block 0
import numpy as np

# Locate both cubes
red_pos, red_quat, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_extent = get_object_pose("green cube", return_bbox_extent=True)

red_half_h = red_extent[2] / 2.0
green_half_h = green_extent[2] / 2.0

# Grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Pick up the red cube
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift to a safe height (at least +0.2 m in Z)
lift_pos = np.array([grasp_pos[0], grasp_pos[1], grasp_pos[2] + 0.2])
goto_pose(lift_pos, grasp_quat)

# Move laterally above the green cube at the same safe height
safe_z = lift_pos[2]
above_green = np.array([green_pos[0], green_pos[1], safe_z])
goto_pose(above_green, grasp_quat)

# Compute stacking height: place red cube on top of green cube
place_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Descend onto the green cube with controlled approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube
open_gripper()

# Retreat upward to a safe height after release
retreat_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.2])
goto_pose(retreat_pos, grasp_quat)