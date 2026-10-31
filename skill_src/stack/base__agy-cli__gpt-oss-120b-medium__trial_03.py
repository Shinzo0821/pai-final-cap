# Code block 0
import numpy as np

# Parameters
z_approach = 0.1          # approach offset
lift_height = 0.2         # safe lift after grasp

# 1. Get poses and extents
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# 2. Sample a grasp pose for the red cube (use its quaternion)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# 3. Approach the red cube and grasp
goto_pose(grasp_pos, grasp_quat, z_approach=z_approach)
open_gripper()
close_gripper()

# 4. Lift the red cube to a safe height
lift_pos = grasp_pos + np.array([0.0, 0.0, lift_height])
goto_pose(lift_pos, grasp_quat, z_approach=0.0)

# 5. Compute placement height on top of the green cube
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# 6. Approach the placement location and release
goto_pose(place_pos, grasp_quat, z_approach=z_approach)
open_gripper()

# 7. Retreat to a safe height
retreat_pos = place_pos + np.array([0.0, 0.0, lift_height])
goto_pose(retreat_pos, grasp_quat, z_approach=0.0)