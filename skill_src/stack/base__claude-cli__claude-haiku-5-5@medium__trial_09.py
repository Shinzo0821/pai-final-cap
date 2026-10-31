# Code block 0
import numpy as np

# Query object poses (red cube to pick, green cube as placement target)
red_pos, red_quat, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Grasp pose for the red cube (use its quaternion for all gripper orientations)
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Compute stacking placement height on top of the green cube
place_z = green_pos[2] + green_extent[2] / 2 + red_extent[2] / 2
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Ensure gripper is open before approaching
open_gripper()

# Approach the grasp pose from above with controlled descent
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close gripper to grasp the red cube
close_gripper()

# Lift to a safe height (at least +0.2 m) before lateral motion
lift_pos = np.array([grasp_pos[0], grasp_pos[1], grasp_pos[2] + 0.2])
goto_pose(lift_pos, grasp_quat)

# Move laterally above the green cube at the safe height
safe_place_above = np.array([green_pos[0], green_pos[1], lift_pos[2]])
goto_pose(safe_place_above, grasp_quat)

# Lower onto the green cube with controlled approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube
open_gripper()

# Retreat upward to clear the stack
retreat_pos = np.array([place_pos[0], place_pos[1], place_pos[2] + 0.2])
goto_pose(retreat_pos, grasp_quat)