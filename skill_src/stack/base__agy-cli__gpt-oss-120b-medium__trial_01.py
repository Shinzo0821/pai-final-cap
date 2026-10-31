# Code block 0
import numpy as np

# Parameters
z_approach = 0.1          # approach offset
lift_height = 0.2         # lift after grasping (meters)

# 1. Open gripper before grasping
open_gripper()

# 2. Get poses and extents for red and green cubes
red_pos, red_quat, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# 3. Sample a reliable grasp pose for the red cube (use its quaternion)
red_grasp_pos, red_grasp_quat = sample_grasp_pose("red cube")

# 4. Approach the red cube and close the gripper
goto_pose(red_grasp_pos, red_grasp_quat, z_approach=z_approach)
close_gripper()

# 5. Lift the red cube to a safe height
lifted_pos = red_grasp_pos.copy()
lifted_pos[2] += lift_height
goto_pose(lifted_pos, red_grasp_quat, z_approach=0.0)

# 6. Compute stacking placement height
place_z = (
    green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
)

# 7. Define placement pose (same X,Y as green cube, computed Z, same orientation as grasp)
place_pos = np.array([green_pos[0], green_pos[1], place_z])
place_quat = red_grasp_quat  # reuse grasp orientation

# 8. Approach the placement position and release the cube
goto_pose(place_pos, place_quat, z_approach=z_approach)
open_gripper()

# 9. Retract to a safe height after release
retract_pos = place_pos.copy()
retract_pos[2] += lift_height
goto_pose(retract_pos, place_quat, z_approach=0.0)