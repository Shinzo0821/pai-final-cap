# Code block 0
import numpy as np

# Look up both cubes: positions and full side-length extents
red_pos, red_quat, red_ext = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_ext = get_object_pose("green cube", return_bbox_extent=True)

# Grasp pose for the red cube (reuse this quaternion for placement too)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Safe transit height: at least 0.2 m above the grasp height
safe_z = max(grasp_pos[2] + 0.2, 0.3)

# Make sure the gripper is open before approaching
open_gripper()

# Approach the grasp pose from above
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close gripper to grab the red cube
close_gripper()

# Lift straight up to a safe height
lift_pos = np.array([grasp_pos[0], grasp_pos[1], safe_z])
goto_pose(lift_pos, grasp_quat)

# Compute placement position on top of the green cube
# place_z = green_center_z + green_extent[2]/2 + red_extent[2]/2
place_z = green_pos[2] + green_ext[2] / 2 + red_ext[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Move laterally above the green cube at safe height
above_place = np.array([place_pos[0], place_pos[1], safe_z])
goto_pose(above_place, grasp_quat)

# Controlled descent onto the green cube using z_approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the cube
open_gripper()

# Retreat upward to a safe height after release
retreat_pos = np.array([place_pos[0], place_pos[1], safe_z])
goto_pose(retreat_pos, grasp_quat)