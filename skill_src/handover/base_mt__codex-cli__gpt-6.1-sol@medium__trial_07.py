# Code block 0
import numpy as np

q0_pick = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1_transfer = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

open_gripper_arm1()
goto_pose_arm1(np.array([1.18, 0.0, 0.45]), q1_transfer)
p1 = np.array([1.18, 0.0, 0.45])

open_gripper_arm0()
goto_pose_arm0(np.array([0.44, 0.0, 0.45]), q0_pick)
p0 = np.array([0.44, 0.0, 0.45])

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

# Grasp the head-side portion of the handle, leaving its tip for Arm 1.
grasp = hammer + np.array([0.0, -0.052, 0.0])
overhead = grasp.copy()
overhead[2] = max(0.40, grasp[2] + 0.20)
p0 = translate(goto_pose_arm0, p0, overhead, q0_pick)
p0 = translate(goto_pose_arm0, p0, grasp, q0_pick, step=0.01)
close_gripper_arm0()

lifted = p0.copy()
lifted[2] = max(0.40, p0[2] + 0.22)
p0 = translate(goto_pose_arm0, p0, lifted, q0_pick)

# Rotate in place, above the table, so the free handle points toward Arm 1.
# Rotation and translation are deliberately performed separately.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    quaternion = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (s + c) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(p0, quaternion)

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
held_offset = hammer - p0

# Put the handle midpoint at the midpoint between the robots.
target_center = np.array([0.81, 0.0, 0.175])
transfer_pose = target_center - held_offset
travel_pose = transfer_pose.copy()
travel_pose[2] = p0[2]
p0 = translate(goto_pose_arm0, p0, travel_pose, q0_transfer)
p0 = translate(goto_pose_arm0, p0, transfer_pose, q0_transfer, step=0.01)

# Correct the hammer height using its measured position before approaching.
for _ in range(2):
    hammer, _ = get_hammer_pose()
    hammer = np.asarray(hammer, dtype=float)
    correction = target_center - hammer
    if np.linalg.norm(correction) < 0.002:
        break
    p0 = translate(
        goto_pose_arm0, p0, p0 + correction, q0_transfer, step=0.01
    )

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
if not 0.15 <= hammer[2] <= 0.20:
    raise RuntimeError("Hammer is outside the permitted handover height.")

receiver = hammer + np.array([0.052, 0.0, 0.0])
if np.linalg.norm((receiver - p0)[:2]) < 0.09:
    raise RuntimeError("Insufficient gripper separation for a safe handover.")

# Approach from above on the right; the grasp sites are about 10.4 cm apart.
receiver_above = receiver.copy()
receiver_above[2] = max(p1[2], receiver[2] + 0.20)
p1 = translate(goto_pose_arm1, p1, receiver_above, q1_transfer)
p1 = translate(
    goto_pose_arm1, p1, receiver, q1_transfer, step=0.01
)

# Establish receiver support before releasing the donor over the central gap.
close_gripper_arm1()
open_gripper_arm0()

# Withdraw vertically first to avoid sweeping into the hammer head.
clearance = p0 + np.array([0.0, 0.0, 0.18])
p0 = translate(goto_pose_arm0, p0, clearance, q0_transfer, step=0.01)
retreat = p0.copy()
retreat[0] = 0.44
p0 = translate(goto_pose_arm0, p0, retreat, q0_transfer)