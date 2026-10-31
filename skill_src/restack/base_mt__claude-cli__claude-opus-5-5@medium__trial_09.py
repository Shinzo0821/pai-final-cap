# Code block 0
import numpy as np

# Get the poses and extents of both cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample a grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Offset between the grasp point and the red cube's center (along z)
grasp_offset_z = grasp_pos[2] - red_pos[2]

# Open the gripper, approach from above, and grasp the red cube
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the red cube straight up
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Compute the placement height:
# top of green cube = green center z + half of green height
# red cube center should sit half of red height above that
green_top_z = green_pos[2] + green_extent[2] / 2.0
target_red_center_z = green_top_z + red_extent[2] / 2.0
clearance = 0.003  # small clearance so it is set down gently, not pressed in or dropped

place_pos = np.array([
    green_pos[0],
    green_pos[1],
    target_red_center_z + grasp_offset_z + clearance,
])

# Move above the green cube, then descend slowly to the placement pose
above_place = place_pos.copy()
above_place[2] += 0.15
goto_pose(above_place, grasp_quat)
goto_pose(place_pos, grasp_quat, z_approach=0.05)

# Release the red cube on top of the green cube
open_gripper()

# Retreat upward
retreat_pos = place_pos.copy()
retreat_pos[2] += 0.1
goto_pose(retreat_pos, grasp_quat)

# Code block 1
import numpy as np

# Verification only: query the final state without moving the robot
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

green_top_z = green_pos[2] + green_extent[2] / 2.0
expected_red_center_z = green_top_z + red_extent[2] / 2.0

xy_offset = np.linalg.norm(red_pos[:2] - green_pos[:2])
z_error = red_pos[2] - expected_red_center_z

print("red_pos:", red_pos, "red_extent:", red_extent)
print("green_pos:", green_pos, "green_extent:", green_extent)
print("xy offset (m):", xy_offset)
print("z error vs expected stacked height (m):", z_error)
print("stacked:", xy_offset < max(green_extent[0], green_extent[1]) / 2.0 and abs(z_error) < 0.01)

# Code block 2
import numpy as np

def get_state():
    r_pos, _, r_ext = get_object_pose("red cube", return_bbox_extent=True)
    g_pos, _, g_ext = get_object_pose("green cube", return_bbox_extent=True)
    return np.array(r_pos), np.array(r_ext), np.array(g_pos), np.array(g_ext)

red_pos, red_extent, green_pos, green_extent = get_state()
print("initial red:", red_pos, "green:", green_pos)

success = False
for attempt in range(4):
    red_pos, red_extent, green_pos, green_extent = get_state()
    red_z_before = red_pos[2]

    # Sample a grasp; fall back to a top-down grasp at the cube center if it looks off
    grasp_pos, grasp_quat = sample_grasp_pose("red cube")
    grasp_pos = np.array(grasp_pos, dtype=float)
    grasp_quat = np.array(grasp_quat, dtype=float)
    if np.linalg.norm(grasp_pos[:2] - red_pos[:2]) > 0.02 or attempt >= 2:
        grasp_pos = red_pos.copy()
        grasp_quat = np.array([0.0, 0.0, 1.0, 0.0])
    print("attempt", attempt, "grasp_pos:", grasp_pos, "quat:", grasp_quat)

    grasp_offset_z = grasp_pos[2] - red_pos[2]

    # Approach and grasp
    open_gripper()
    goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
    close_gripper()

    # Lift
    lift_pos = grasp_pos.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)

    red_lifted, _, _ = get_object_pose("red cube", return_bbox_extent=True)
    print("red after lift:", red_lifted)
    if red_lifted[2] - red_z_before < 0.05:
        print("Grasp failed, retrying")
        open_gripper()
        continue

    # Compute exact placement height from extents
    green_top_z = green_pos[2] + green_extent[2] / 2.0
    target_red_center_z = green_top_z + red_extent[2] / 2.0
    clearance = 0.003
    place_pos = np.array([
        green_pos[0],
        green_pos[1],
        target_red_center_z + grasp_offset_z + clearance,
    ])

    # Move above green cube, then descend gently
    above_place = place_pos.copy()
    above_place[2] = max(lift_pos[2], place_pos[2] + 0.12)
    goto_pose(above_place, grasp_quat)
    goto_pose(place_pos, grasp_quat, z_approach=0.05)

    # Release and retreat
    open_gripper()
    retreat_pos = place_pos.copy()
    retreat_pos[2] += 0.1
    goto_pose(retreat_pos, grasp_quat)

    red_pos, red_extent, green_pos, green_extent = get_state()
    green_top_z = green_pos[2] + green_extent[2] / 2.0
    expected = green_top_z + red_extent[2] / 2.0
    xy_off = np.linalg.norm(red_pos[:2] - green_pos[:2])
    z_err = red_pos[2] - expected
    print("final red:", red_pos, "green:", green_pos, "xy_off:", xy_off, "z_err:", z_err)
    if xy_off < green_extent[0] / 2.0 and abs(z_err) < 0.01:
        success = True
        break

print("stacked:", success)