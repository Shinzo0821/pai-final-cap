# Code block 0
import numpy as np

# Get the pose and bounding box extent of the red cube and green cube
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Calculate the Z offset between the grasp position and the red cube's center
grasp_z_offset = grasp_pos[2] - red_pos[2]

# Open the gripper before approaching the red cube
open_gripper()

# Approach and move to the grasp pose of the red cube
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close the gripper to grasp the red cube
close_gripper()

# Lift the red cube straight up to avoid collisions during transit
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Calculate the target center position for the red cube on top of the green cube
# The bottom of the red cube should rest on the top of the green cube:
# target_red_center_z = green_center_z + (green_height / 2) + (red_height / 2)
target_red_center_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)

# Account for the gripper's grasp offset relative to the red cube's center,
# plus a tiny clearance (e.g., 2mm) to gently place without pressing down too hard
place_pos = np.array([
    green_pos[0],
    green_pos[1],
    target_red_center_z + grasp_z_offset + 0.002
])

# Move above the green cube and gently lower the red cube onto it using z_approach
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Open the gripper to release the red cube
open_gripper()

# Retract the gripper upwards after releasing
retract_pos = place_pos.copy()
retract_pos[2] += 0.1
goto_pose(retract_pos, grasp_quat)

# Code block 1
# Query the current poses and extents of the cubes to verify if the red cube is on top of the green cube
red_pos_after, _, red_extent_after = get_object_pose("red cube", return_bbox_extent=True)
green_pos_after, _, green_extent_after = get_object_pose("green cube", return_bbox_extent=True)

expected_z = green_pos_after[2] + (green_extent_after[2] / 2.0) + (red_extent_after[2] / 2.0)
xy_dist = np.linalg.norm(red_pos_after[:2] - green_pos_after[:2])
z_diff = abs(red_pos_after[2] - expected_z)

print(f"Red pos: {red_pos_after}, Green pos: {green_pos_after}")
print(f"XY distance: {xy_dist:.4f}, Z diff from expected ({expected_z:.4f}): {z_diff:.4f}")

# If the red cube is not properly stacked on the green cube, retry the pick and place
if xy_dist > 0.03 or z_diff > 0.02:
    print("Task not yet complete, retrying...")
    grasp_pos, grasp_quat = sample_grasp_pose("red cube")
    grasp_offset = grasp_pos - red_pos_after

    open_gripper()
    goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
    close_gripper()

    lift_pos = grasp_pos.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)

    target_red_center = np.array([
        green_pos_after[0],
        green_pos_after[1],
        expected_z + 0.002
    ])
    place_pos = target_red_center + grasp_offset

    goto_pose(place_pos, grasp_quat, z_approach=0.1)
    open_gripper()

    retract_pos = place_pos.copy()
    retract_pos[2] += 0.1
    goto_pose(retract_pos, grasp_quat)
    
    # Re-verify after retry
    red_pos_final, _, _ = get_object_pose("red cube", return_bbox_extent=False)
    green_pos_final, _, _ = get_object_pose("green cube", return_bbox_extent=False)
    print(f"After retry - Red pos: {red_pos_final}, Green pos: {green_pos_final}")
else:
    print("Task successfully completed!")