# Code block 0
import numpy as np

q0 = np.array([0.0, 1.0 / np.sqrt(2), 1.0 / np.sqrt(2), 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])
hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
offset = 0.055
handover_center = np.array([0.81, 0.0, 0.175])
clearance_z = max(0.40, hammer_initial[2] + 0.22)

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quaternion)
    return end.copy()

# Park the receiving arm away from the pickup and rotation workspace.
open_gripper_arm1()
receiver = np.array([1.18, 0.0, clearance_z + 0.10])
goto_pose_arm1(receiver, q1)

# Both grasp sites remain on even the shortest handle, 11 cm apart.
open_gripper_arm0()
pickup = hammer_initial + np.array([0.0, -offset, 0.0])
donor = pickup.copy()
donor[2] = clearance_z
goto_pose_arm0(donor, q0)
donor = translate(goto_pose_arm0, donor, pickup, q0)
close_gripper_arm0()

lifted = donor.copy()
lifted[2] = clearance_z
donor = translate(goto_pose_arm0, donor, lifted, q0)
hammer_lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if hammer_lifted[2] < hammer_initial[2] + 0.08:
    raise RuntimeError("Pickup did not lift the hammer; aborting before the gap.")

# Rotate in place above the pickup area, independently of translation.
# A -90-degree world-Z rotation points the free handle end toward Arm 1.
for angle in np.linspace(0.0, -np.pi / 2, 19)[1:]:
    c, s = np.cos(angle / 2), np.sin(angle / 2)
    quaternion = np.array([
        0.0,
        (c - s) / np.sqrt(2),
        (c + s) / np.sqrt(2),
        0.0,
    ])
    goto_pose_arm0(donor, quaternion)
q0 = np.array([0.0, 1.0, 0.0, 0.0])

# Carry high, then lower vertically; use measured handle-center position.
center = np.asarray(get_hammer_pose()[0], dtype=float)
high_center = handover_center.copy()
high_center[2] = clearance_z
donor = translate(goto_pose_arm0, donor, donor + high_center - center, q0)

center = np.asarray(get_hammer_pose()[0], dtype=float)
donor = translate(
    goto_pose_arm0, donor, donor + handover_center - center, q0
)

for _ in range(3):
    center = np.asarray(get_hammer_pose()[0], dtype=float)
    correction = handover_center - center
    if np.linalg.norm(correction) < 0.003:
        break
    donor = translate(goto_pose_arm0, donor, donor + correction, q0)

center = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= center[2] <= 0.20:
    raise RuntimeError("Hammer is outside the required handover height.")

receive = center + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receive[:2] - donor[:2]) < 0.09:
    raise RuntimeError("Insufficient clearance between grippers.")

# Approach from above with fixed orientation, preserving horizontal clearance.
above_receive = receive.copy()
above_receive[2] = clearance_z + 0.10
receiver = translate(goto_pose_arm1, receiver, above_receive, q1)
receiver = translate(goto_pose_arm1, receiver, receive, q1)

# Establish the receiving grasp before releasing the supporting grasp.
close_gripper_arm1()
open_gripper_arm0()

retreat = donor.copy()
retreat[2] = clearance_z + 0.10
donor = translate(goto_pose_arm0, donor, retreat, q0)
retreat = donor.copy()
retreat[0] = 0.44
donor = translate(goto_pose_arm0, donor, retreat, q0)