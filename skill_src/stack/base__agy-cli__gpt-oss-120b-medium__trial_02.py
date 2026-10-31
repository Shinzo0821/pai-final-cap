# Code block 0
import numpy as np

# Retrieve poses and extents
red_pos, red_quat, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a reliable grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Open gripper before approaching
open_gripper()

# Approach the red cube with a safe z offset and grasp
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube to a safe height (+0.2 m in Z)
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.2])
goto_pose(lift_pos, grasp_quat)

# Compute stacking placement height
place_z = (
    green_pos[2]               # green cube center Z
    + green_extent[2] / 2      # half of green cube height
    + red_extent[2] / 2        # half of red cube height
)

# Placement position directly above the green cube
place_pos = np.array([green_pos[0], green_pos[1], place_z])

# Approach the placement position using the same grasp orientation
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Release the red cube onto the green cube
open_gripper()