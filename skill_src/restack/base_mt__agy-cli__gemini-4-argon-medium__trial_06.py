# Code block 0
import numpy as np

# Open the gripper before starting
open_gripper()

# Get the pose and bounding box extent of the red cube and the green cube
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Calculate the Z offset between the grasp pose and the red cube's center
grasp_z_offset = grasp_pos[2] - red_pos[2]

# Move to grasp the red cube with a safe Z-approach and close the gripper
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube straight up to avoid collisions during horizontal movement
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Calculate the exact target center Z for the red cube when resting on top of the green cube
# Top of green cube = green_pos[2] + green_extent[2] / 2.0
# Center of red cube on top = top of green cube + red_extent[2] / 2.0
target_red_center_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)

# Account for the grasp offset so the gripper places the red cube at the exact target height
place_pos = np.array([
    green_pos[0],
    green_pos[1],
    target_red_center_z + grasp_z_offset
])

# Gently approach from above and lower the red cube onto the green cube
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Open the gripper to release the red cube gently
open_gripper()

# Retract the gripper upwards after releasing
retract_pos = place_pos.copy()
retract_pos[2] += 0.1
goto_pose(retract_pos, grasp_quat)

# Code block 1
import numpy as np

# Check the current poses and extents of the red cube and the green cube to verify if the task is complete
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

expected_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)
xy_dist = np.linalg.norm(red_pos[:2] - green_pos[:2])
z_diff = abs(red_pos[2] - expected_z)

print(f"Red pos: {red_pos}, Green pos: {green_pos}, Expected Z: {expected_z}")
print(f"XY dist: {xy_dist:.4f}, Z diff: {z_diff:.4f}")

# If the red cube is not properly stacked on top of the green cube, retry the pick and place
if xy_dist > 0.03 or z_diff > 0.02:
    print("Task not yet complete, retrying pick and place...")
    open_gripper()

    grasp_pos, grasp_quat = sample_grasp_pose("red cube")
    grasp_z_offset = grasp_pos[2] - red_pos[2]

    goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
    close_gripper()

    lift_pos = grasp_pos.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)

    green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
    target_red_center_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)

    place_pos = np.array([
        green_pos[0],
        green_pos[1],
        target_red_center_z + grasp_z_offset + 0.002
    ])

    goto_pose(place_pos, grasp_quat, z_approach=0.1)
    open_gripper()

    retract_pos = place_pos.copy()
    retract_pos[2] += 0.1
    goto_pose(retract_pos, grasp_quat)

    red_pos_after, _, _ = get_object_pose("red cube", return_bbox_extent=False)
    print(f"After retry - Red pos: {red_pos_after}")
else:
    print("Task successfully completed!")

# Code block 2
import numpy as np

# Check the current poses and extents of both cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

expected_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)
xy_dist = np.linalg.norm(red_pos[:2] - green_pos[:2])
z_diff = abs(red_pos[2] - expected_z)

print(f"Red pos: {red_pos}, Red extent: {red_extent}")
print(f"Green pos: {green_pos}, Green extent: {green_extent}")
print(f"Expected Z: {expected_z}, XY dist: {xy_dist:.4f}, Z diff: {z_diff:.4f}")

# If not properly stacked, perform pick and place accounting for full 3D grasp offset
if xy_dist > 0.025 or z_diff > 0.015:
    open_gripper()

    red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
    grasp_pos, grasp_quat = sample_grasp_pose("red cube")

    # Full 3D offset between grasp point and red cube center
    grasp_offset = grasp_pos - red_pos

    goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
    close_gripper()

    lift_pos = grasp_pos.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)

    green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
    target_red_center = np.array([
        green_pos[0],
        green_pos[1],
        green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)
    ])

    # Apply the 3D grasp offset to place the center of the red cube directly over the green cube
    place_pos = target_red_center + grasp_offset
    place_pos[2] += 0.002

    goto_pose(place_pos, grasp_quat, z_approach=0.1)
    open_gripper()

    retract_pos = place_pos.copy()
    retract_pos[2] += 0.1
    goto_pose(retract_pos, grasp_quat)

    red_pos_after, _, _ = get_object_pose("red cube", return_bbox_extent=False)
    green_pos_after, _, _ = get_object_pose("green cube", return_bbox_extent=False)
    print(f"After retry - Red pos: {red_pos_after}, Green pos: {green_pos_after}")