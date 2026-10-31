# Code block 0
import numpy as np

# Get poses and extents
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube (provides a reliable orientation)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper before approaching
open_gripper()

# Approach the red cube and grasp it
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube to a safe height (+0.2 m above its top)
lift_z = red_pos[2] + red_extent[2] / 2 + 0.2
lift_pos = np.array([grasp_pos[0], grasp_pos[1], lift_z])
goto_pose(lift_pos, grasp_quat, z_approach=0.0)

# Compute the placement pose on top of the green cube
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Approach the placement pose and release the cube
goto_pose(place_pos, grasp_quat, z_approach=0.1)
open_gripper()