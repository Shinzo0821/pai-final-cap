# Code block 0
import numpy as np

# Get poses and extents of both cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube and pick it up with an approach from above
grasp_pos, grasp_quat = sample_grasp_pose("red cube")
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube straight up to clear the surface
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Compute placement: red cube center must sit at green top + half red height.
# The gripper-to-cube-center offset is preserved from the grasp, so shift the
# gripper target by the same delta the cube center needs to move.
target_red_center_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
delta_z = target_red_center_z - red_pos[2]
place_pos = np.array([green_pos[0], green_pos[1], grasp_pos[2] + delta_z])

# Move above the green cube, then descend gently to the exact placement height
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube only once it is resting on the green cube
open_gripper()

# Retreat upward
retreat_pos = place_pos.copy()
retreat_pos[2] += 0.1
goto_pose(retreat_pos, grasp_quat)