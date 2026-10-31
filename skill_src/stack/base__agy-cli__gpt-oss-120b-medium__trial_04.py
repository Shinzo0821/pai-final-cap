# Code block 0
import numpy as np

# Get poses and extents
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube
red_grasp_pos, red_grasp_quat = sample_grasp_pose("red cube")

# Approach the red cube and grasp it
goto_pose(red_grasp_pos, red_grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube to a safe height (+0.2 m in Z)
lift_pos = red_grasp_pos.copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, red_grasp_quat)

# Compute the placement position on top of the green cube
place_xy = green_pos[:2]
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([place_xy[0], place_xy[1], place_z])

# Approach the placement location and release the cube
goto_pose(place_pos, red_grasp_quat, z_approach=0.1)
open_gripper()

# Retract the gripper upward slightly
retract_pos = place_pos.copy()
retract_pos[2] += 0.1
goto_pose(retract_pos, red_grasp_quat)