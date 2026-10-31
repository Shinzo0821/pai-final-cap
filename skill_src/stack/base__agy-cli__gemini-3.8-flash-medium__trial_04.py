# Code block 0
import numpy as np

# Get poses and bounding box extents of the red and green cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper before grasping
open_gripper()

# Approach and grasp the red cube
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the cube to a safe height (+0.2m in Z) before moving laterally
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

# Calculate placement position on top of the green cube
place_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Approach and place gently using grasp quaternion and z_approach, then release
goto_pose(place_pos, grasp_quat, z_approach=0.1)
open_gripper()