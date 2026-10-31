# Code block 0
import numpy as np

# Get grasp pose for the red cube and pick it up with an approach from above
grasp_pos, grasp_quat = sample_grasp_pose("red cube")
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift the red cube
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Get poses and extents of both cubes
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Compute placement: red cube center should sit at green top + half red height.
# The gripper holds the red cube at grasp_pos; offset between grasp and red cube center is preserved.
grasp_offset_z = grasp_pos[2] - red_pos[2]
green_top_z = green_pos[2] + green_extent[2] / 2.0
place_center_z = green_top_z + red_extent[2] / 2.0
place_pos = np.array([green_pos[0], green_pos[1], place_center_z + grasp_offset_z + 0.005])

# Move above the green cube, then descend gently and release
goto_pose(place_pos, grasp_quat, z_approach=0.10)
open_gripper()

# Retreat upward
retreat_pos = place_pos.copy()
retreat_pos[2] += 0.10
goto_pose(retreat_pos, grasp_quat)

# Code block 1
import numpy as np

# Verify final state without moving the robot
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

print("red_pos:", red_pos, "red_extent:", red_extent)
print("green_pos:", green_pos, "green_extent:", green_extent)

xy_err = np.linalg.norm(red_pos[:2] - green_pos[:2])
expected_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
z_err = red_pos[2] - expected_z
print("xy offset (m):", xy_err)
print("z error vs expected stacked height (m):", z_err)
print("stacked:", xy_err < 0.02 and abs(z_err) < 0.01)

# Code block 2
import numpy as np

down_quat = np.array([0.0, 0.0, 1.0, 0.0])

def stacked_ok():
    r, _, re = get_object_pose("red cube", return_bbox_extent=True)
    g, _, ge = get_object_pose("green cube", return_bbox_extent=True)
    xy = np.linalg.norm(r[:2] - g[:2])
    z_exp = g[2] + ge[2] / 2.0 + re[2] / 2.0
    return xy < 0.02 and abs(r[2] - z_exp) < 0.01, xy, r[2] - z_exp

for attempt in range(3):
    # Re-sample grasp since cube position may have changed
    red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
    grasp_pos, grasp_quat = sample_grasp_pose("red cube")
    open_gripper()
    goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
    close_gripper()

    # Lift and verify the cube actually came along
    lift_pos = grasp_pos.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)
    red_now, _, _ = get_object_pose("red cube", return_bbox_extent=True)
    print("attempt", attempt, "red z after lift:", red_now[2], "before:", red_pos[2])
    if red_now[2] - red_pos[2] < 0.05:
        print("grasp failed, retrying")
        open_gripper()
        continue

    # Place using the offset between gripper and cube center (held)
    green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
    grasp_offset_z = lift_pos[2] - red_now[2]
    place_center_z = green_pos[2] + green_extent[2] / 2.0 + red_extent[2] / 2.0
    place_pos = np.array([green_pos[0], green_pos[1], place_center_z + grasp_offset_z + 0.003])

    goto_pose(place_pos, grasp_quat, z_approach=0.10)
    open_gripper()

    retreat_pos = place_pos.copy()
    retreat_pos[2] += 0.10
    goto_pose(retreat_pos, grasp_quat)

    ok, xy, dz = stacked_ok()
    print("stacked:", ok, "xy:", xy, "dz:", dz)
    if ok:
        break