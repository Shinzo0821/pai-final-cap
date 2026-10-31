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

### Example 3: two-arm hammer handover
Goal of that task: Arm 0 picks up the hammer, lifts it and hands it over to Arm 1, which grasps the handle; the hammer must stay at z between 0.15 and 0.20 during the handover.
APIs of that task: get_hammer_pose, goto_pose_arm0, goto_pose_arm1, open_gripper_arm0, open_gripper_arm1, close_gripper_arm0, close_gripper_arm1
```python
import numpy as np

def translate(move, start, end, quat, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quat)
    return end.copy()

q0 = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
safe_z = max(0.40, hammer[2] + 0.20)

open_gripper_arm1()
park1 = np.array([1.18, 0.0, safe_z + 0.10])
goto_pose_arm1(park1, q1)

# Grasp the head-side portion of the handle, leaving its tip available.
open_gripper_arm0()
grasp0 = hammer + np.array([0.0, -0.05, 0.0])
above0 = grasp0.copy()
above0[2] = safe_z
goto_pose_arm0(above0, q0)
pos0 = translate(goto_pose_arm0, above0, grasp0, q0)
close_gripper_arm0()

lifted0 = pos0.copy()
lifted0[2] = safe_z
pos0 = translate(goto_pose_arm0, pos0, lifted0, q0)

# Rotate in place at clearance height. The handle now points toward Arm 1.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    theta = np.pi / 4.0 + angle / 2.0
    q0 = np.array([0.0, np.cos(theta), np.sin(theta), 0.0])
    goto_pose_arm0(pos0, q0)

# Position the handle midpoint at the midpoint between the robots.
hammer_now, _ = get_hammer_pose()
hammer_now = np.asarray(hammer_now, dtype=float)
center_high = np.array([0.81, 0.0, safe_z])
destination0 = pos0 + center_high - hammer_now

lateral0 = destination0.copy()
lateral0[2] = pos0[2]
pos0 = translate(goto_pose_arm0, pos0, lateral0, q0)
pos0 = translate(goto_pose_arm0, pos0, destination0, q0)

hammer_now, _ = get_hammer_pose()
handover_center = np.array([0.81, 0.0, 0.175])
destination0 = pos0 + handover_center - np.asarray(hammer_now)
pos0 = translate(goto_pose_arm0, pos0, destination0, q0)

# The two handle grasps are approximately 10 cm apart.
hammer_now, _ = get_hammer_pose()
hammer_now = np.asarray(hammer_now, dtype=float)
grasp1 = hammer_now + np.array([0.05, 0.0, 0.0])
above1 = grasp1.copy()
above1[2] = park1[2]

pos1 = translate(goto_pose_arm1, park1, above1, q1)
pos1 = translate(goto_pose_arm1, pos1, grasp1, q1)
close_gripper_arm1()

# Release only after Arm 1 has closed on the handle.
open_gripper_arm0()
retreat0 = pos0 + np.array([0.0, 0.0, 0.18])
pos0 = translate(goto_pose_arm0, pos0, retreat0, q0)
translate(goto_pose_arm0, pos0, pos0 + np.array([-0.15, 0.0, 0.0]), q0)
```

(End of reference examples. Now write the code for the current task described above.)
