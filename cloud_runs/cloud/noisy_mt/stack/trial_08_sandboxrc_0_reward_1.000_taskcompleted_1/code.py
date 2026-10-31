# Code block 0
import numpy as np

# Get grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper and approach the red cube from above, then grasp
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube to a safe height
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

# Get poses and extents of both cubes
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)

# Compute placement position on top of the green cube
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move laterally at safe height above the placement location
above_place = place_pos.copy()
above_place[2] = lift_pos[2]
goto_pose(above_place, grasp_quat)

# Descend with controlled approach and release
goto_pose(place_pos, grasp_quat, z_approach=0.1)
open_gripper()

# Retreat upward
retreat_pos = place_pos.copy()
retreat_pos[2] += 0.2
goto_pose(retreat_pos, grasp_quat)