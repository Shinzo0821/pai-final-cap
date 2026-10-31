# Code block 0
import numpy as np

# Parameters
z_approach = 0.1  # approach offset in meters
lift_height = 0.2  # additional lift after grasping

# Get poses and extents
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a reliable grasp pose for the red cube
red_grasp_pos, red_grasp_quat = sample_grasp_pose("red cube")

# Approach the red cube and grasp it
goto_pose(red_grasp_pos, red_grasp_quat, z_approach=z_approach)
close_gripper()

# Lift the red cube to a safe height
lift_pos = red_grasp_pos + np.array([0.0, 0.0, lift_height])
goto_pose(lift_pos, red_grasp_quat, z_approach=0.0)

# Compute placement position above the green cube
place_xy = green_pos[:2]                # keep green cube X,Y
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([place_xy[0], place_xy[1], place_z])

# Approach the placement position and release the cube
goto_pose(place_pos, red_grasp_quat, z_approach=z_approach)
open_gripper()

# Retract to safe height after release
retract_pos = place_pos + np.array([0.0, 0.0, lift_height])
goto_pose(retract_pos, red_grasp_quat, z_approach=0.0)