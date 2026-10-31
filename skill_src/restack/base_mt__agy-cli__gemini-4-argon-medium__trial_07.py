# Code block 0
import numpy as np

# Get the pose and bounding box extent of the red cube and green cube
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Calculate the Z offset between the grasp position and the center of the red cube
grasp_z_offset = grasp_pos[2] - red_pos[2]

# Open the gripper before grasping
open_gripper()

# Approach and move to the grasp pose for the red cube
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close the gripper to grasp the red cube
close_gripper()

# Lift the red cube up vertically to avoid collisions during transport
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Calculate the exact center position of the red cube when resting on top of the green cube:
# green_pos[2] + green_extent[2] / 2.0 (top surface of green cube) + red_extent[2] / 2.0 (half height of red cube)
target_red_center_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)

# Account for the gripper's grasp offset relative to the red cube's center, plus a tiny 1mm margin for gentle contact
place_pos = np.array([
    green_pos[0],
    green_pos[1],
    target_red_center_z + grasp_z_offset + 0.001
])

# Move above the green cube and gently lower the red cube onto it using z_approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Open the gripper to release the red cube gently
open_gripper()

# Retract the gripper upwards after releasing
retract_pos = place_pos.copy()
retract_pos[2] += 0.1
goto_pose(retract_pos, grasp_quat)

# Code block 1
import numpy as np

# Check the current poses and extents of the red cube and green cube to verify task completion
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

expected_red_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)
xy_dist = np.linalg.norm(red_pos[:2] - green_pos[:2])
z_diff = abs(red_pos[2] - expected_red_z)

print(f"Red pos: {red_pos}, Green pos: {green_pos}")
print(f"XY dist: {xy_dist:.4f}, Z diff: {z_diff:.4f}")

# If the red cube is not on top of the green cube, execute the pick and place again
if xy_dist > 0.03 or z_diff > 0.03:
    grasp_pos, grasp_quat = sample_grasp_pose("red cube")
    grasp_offset = grasp_pos - red_pos

    open_gripper()
    goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
    close_gripper()

    lift_pos = grasp_pos.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)

    target_red_center = np.array([
        green_pos[0],
        green_pos[1],
        expected_red_z + 0.002
    ])
    place_pos = target_red_center + grasp_offset

    goto_pose(place_pos, grasp_quat, z_approach=0.1)
    open_gripper()

    retract_pos = place_pos.copy()
    retract_pos[2] += 0.1
    goto_pose(retract_pos, grasp_quat)

    red_pos_after, _, _ = get_object_pose("red cube", return_bbox_extent=False)
    print(f"Red pos after retry: {red_pos_after}")