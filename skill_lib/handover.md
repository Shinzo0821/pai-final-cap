Reference examples (skill library):
The programs below are complete solutions that SUCCEEDED on OTHER tasks of this benchmark (written by stronger models).
They are not solutions for the current task. Reuse their patterns where they fit, for example: computing heights from object extents,
keeping the grasp offset between the gripper and the object, rigid transforms with scipy, safe approach / lift / step-wise motions,
and checking the state with prints before finishing.
They were written for other objects and possibly other APIs: call ONLY the APIs listed for the current task below.

### Example 1: cube stacking (single arm)
Goal of that task: Pick up the red cube and gently stack it on top of the green cube, then release it.
APIs of that task: get_object_pose, sample_grasp_pose, goto_pose, open_gripper, close_gripper
```python
import numpy as np

red_center, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_center, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
grasp_position, grasp_quaternion = sample_grasp_pose("red cube")

grasp_offset = np.asarray(grasp_position) - np.asarray(red_center)
place_z = green_center[2] + green_extent[2] / 2 + red_extent[2] / 2
place_position = np.array([green_center[0], green_center[1], place_z]) + grasp_offset

open_gripper()
goto_pose(grasp_position, grasp_quaternion, z_approach=0.1)
close_gripper()

lift_position = np.array(grasp_position, dtype=float, copy=True)
lift_position[2] = max(grasp_position[2] + 0.2, place_position[2] + 0.1)
goto_pose(lift_position, grasp_quaternion)

goto_pose(place_position, grasp_quaternion, z_approach=0.1)
open_gripper()
```

### Example 2: cube restacking (single arm)
Goal of that task: Gently place the red cube on top of the green cube and then open the gripper (at the start the cubes may already be stacked the other way round).
APIs of that task: get_object_pose, sample_grasp_pose, goto_pose, open_gripper, close_gripper
```python
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
```

### Example 3: nut assembly (single arm)
Goal of that task: Grasp the brown square nut by its handle and insert it onto the brown square block (peg).
APIs of that task: get_object_pose, sample_grasp_pose, goto_pose, goto_home_joint_position, open_gripper, close_gripper
```python
import numpy as np
from scipy.spatial.transform import Rotation

def rotation(q):
    return Rotation.from_quat(np.asarray(q)[[1, 2, 3, 0]]).as_matrix()

def quaternion(r):
    return Rotation.from_matrix(r).as_quat()[[3, 0, 1, 2]]

open_gripper()
nut_p, nut_q = get_object_pose("white hollow center of the brown square nut")
grasp_p, grasp_q = sample_grasp_pose("extruded handle of the brown square nut")
block_p, block_q = get_object_pose("brown square block")

nut_p = np.asarray(nut_p)
grasp_p = np.asarray(grasp_p)
block_p = np.asarray(block_p)
nut_r = rotation(nut_q)
grasp_r = rotation(grasp_q)
block_r = rotation(block_q)

# Fixed handle grasp transform expressed in the nut-center frame.
relative_p = nut_r.T @ (grasp_p - nut_p)
relative_r = nut_r.T @ grasp_r

goto_pose(grasp_p, grasp_q, z_approach=0.10)
close_gripper()
goto_pose(grasp_p + np.array([0.0, 0.0, 0.15]), grasp_q)

target_grasp_p = block_p + block_r @ relative_p
target_grasp_q = quaternion(block_r @ relative_r)

goto_pose(target_grasp_p + np.array([0.0, 0.0, 0.15]), target_grasp_q)
goto_pose(target_grasp_p + np.array([0.0, 0.0, 0.05]), target_grasp_q)
goto_pose(target_grasp_p, target_grasp_q)
open_gripper()
goto_pose(target_grasp_p + np.array([0.0, 0.0, 0.15]), target_grasp_q)
goto_home_joint_position()
```

(End of reference examples. Now write the code for the current task described above.)
