# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0])
q0_pick /= np.linalg.norm(q0_pick)
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
clearance = max(0.40, hammer[2] + 0.22)

open_gripper_arm1()
arm1 = np.array([1.18, 0.0, clearance])
goto_pose_arm1(arm1, q1)

open_gripper_arm0()
arm0 = np.array([0.44, 0.0, clearance])
goto_pose_arm0(arm0, q0_pick)

# Use two handle locations 10 cm apart, within even the shortest handle.
pickup = hammer + np.array([0.0, -0.05, 0.0])
above_pickup = pickup.copy()
above_pickup[2] = clearance
arm0 = translate(goto_pose_arm0, arm0, above_pickup, q0_pick)
arm0 = translate(goto_pose_arm0, arm0, pickup, q0_pick, step=0.01)
close_gripper_arm0()

lifted = arm0.copy()
lifted[2] = clearance
arm0 = translate(goto_pose_arm0, arm0, lifted, q0_pick)

# Rotate in place above the table: the free handle end now points toward +X.
# Keep rotation separate from translation.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    q0 = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(arm0, q0)

# Measure the actual handle-center offset after lifting and rotation.
held_center, _ = get_hammer_pose()
offset = np.asarray(held_center, dtype=float) - arm0
handover_center = np.array([(0.44 + 1.18) / 2.0, 0.0, 0.175])
giver_target = handover_center - offset

high_target = giver_target.copy()
high_target[2] = clearance
arm0 = translate(goto_pose_arm0, arm0, high_target, q0)
arm0 = translate(goto_pose_arm0, arm0, giver_target, q0, step=0.01)

# Correct the hammer height without opening the supporting gripper.
for _ in range(3):
    center, _ = get_hammer_pose()
    center = np.asarray(center, dtype=float)
    correction = handover_center - center
    if np.linalg.norm(correction) < 0.002:
        break
    arm0 = translate(goto_pose_arm0, arm0, arm0 + correction, q0, step=0.01)

center, _ = get_hammer_pose()
center = np.asarray(center, dtype=float)
receiver_target = center + np.array([0.05, 0.0, 0.0])

if not 0.15 <= center[2] <= 0.20:
    raise RuntimeError("Hammer is outside the required handover height.")
if np.linalg.norm(receiver_target[:2] - arm0[:2]) < 0.09:
    raise RuntimeError("Insufficient gripper clearance for a safe transfer.")

receiver_above = receiver_target.copy()
receiver_above[2] = clearance
arm1 = translate(goto_pose_arm1, arm1, receiver_above, q1)
arm1 = translate(goto_pose_arm1, arm1, receiver_target, q1, step=0.01)

# Establish the receiving grasp before releasing support over the gap.
close_gripper_arm1()
open_gripper_arm0()

retreat = arm0 + np.array([-0.12, 0.0, 0.0])
arm0 = translate(goto_pose_arm0, arm0, retreat, q0, step=0.01)
retreat_up = arm0.copy()
retreat_up[2] = clearance
arm0 = translate(goto_pose_arm0, arm0, retreat_up, q0)