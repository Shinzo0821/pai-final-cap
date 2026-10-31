# Code block 0
import numpy as np

# Get poses and bounding box extents for the red and green cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open the gripper before approaching the red cube
open_gripper()

# Approach and move to the grasp pose
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Grasp the red cube
close_gripper()

# Lift the red cube to a safe height (+0.2m in Z)
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

# Calculate the stacking placement position on top of the green cube
place_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move to the placement position with controlled descent using the grasp quaternion
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube
open_gripper()

# Retract upward to clear the stacked cubes
retract_pos = place_pos.copy()
retract_pos[2] += 0.1
goto_pose(retract_pos, grasp_quat)