# Code block 0
import numpy as np

# Get the pose and bounding box extents of the red cube and the green cube
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Calculate the Z offset between the grasp pose and the red cube's center
grasp_z_offset = grasp_pos[2] - red_pos[2]

# Open the gripper before approaching the red cube
open_gripper()

# Move to the grasp pose of the red cube with a top-down approach offset
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close the gripper to grasp the red cube
close_gripper()

# Lift the red cube straight up to safely clear the workspace
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Calculate the exact target center position for the red cube on top of the green cube
# The top surface of the green cube is at green_pos[2] + green_extent[2] / 2.0
# The center of the red cube should be red_extent[2] / 2.0 above that surface
target_red_center_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)

# Account for the gripper's grasp offset relative to the red cube's center,
# plus a tiny clearance (e.g., 1-2 mm) so the cubes gently touch without forceful collision
place_pos = np.array([
    green_pos[0],
    green_pos[1],
    target_red_center_z + grasp_z_offset + 0.002
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

# Check the current poses and bounding box extents of the red cube and the green cube
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

print(f"Red cube pos: {red_pos}, extent: {red_extent}")
print(f"Green cube pos: {green_pos}, extent: {green_extent}")

expected_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)
xy_dist = np.linalg.norm(red_pos[:2] - green_pos[:2])
z_diff = abs(red_pos[2] - expected_z)

print(f"XY distance: {xy_dist:.4f}, Z diff: {z_diff:.4f} (expected Z: {expected_z:.4f})")

# If the red cube is not properly stacked on the green cube, execute the pick and place
if xy_dist > 0.025 or z_diff > 0.02:
    print("Red cube not on green cube yet. Attempting pick and place...")
    grasp_pos, grasp_quat = sample_grasp_pose("red cube")
    grasp_offset = grasp_pos - red_pos

    open_gripper()
    goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
    close_gripper()

    lift_pos = grasp_pos.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)

    # Re-verify green cube pose
    green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
    target_red_center = np.array([
        green_pos[0],
        green_pos[1],
        green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0) + 0.002
    ])
    place_pos = target_red_center + grasp_offset

    goto_pose(place_pos, grasp_quat, z_approach=0.1)
    open_gripper()

    retract_pos = place_pos.copy()
    retract_pos[2] += 0.1
    goto_pose(retract_pos, grasp_quat)

    red_pos_after, _, _ = get_object_pose("red cube", return_bbox_extent=False)
    print(f"Red cube pos after retry: {red_pos_after}")
else:
    print("Task successfully completed!")