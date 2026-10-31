# Code block 0
import numpy as np

# Locate both cubes
red_pos, red_quat, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube and reuse its quaternion for placement
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Grasp the red cube
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift to a safe height (at least +0.2 m) before lateral motion
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.2])
goto_pose(lift_pos, grasp_quat)

# Compute placement position on top of the green cube
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move above the placement location at safe height, then descend with approach offset
safe_place_pos = np.array([place_pos[0], place_pos[1], lift_pos[2]])
goto_pose(safe_place_pos, grasp_quat)
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube
open_gripper()

# Retreat upward to a safe height
retreat_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.2])
goto_pose(retreat_pos, grasp_quat)