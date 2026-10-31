# Code block 0
import numpy as np

Q0_PICK = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
Q0_PASS = np.array([0.0, 1.0, 0.0, 0.0])
Q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
offset = 0.055
clearance_z = max(0.40, hammer_initial[2] + 0.20)
handover_center = np.array([0.81, 0.0, 0.175])

# Park the receiver away from the pickup and rotation workspace.
open_gripper_arm1()
p1 = np.array([1.18, 0.0, clearance_z + 0.10])
goto_pose_arm1(p1, Q1)

# Both contacts remain on the shortest possible handle, 11 cm apart.
open_gripper_arm0()
pickup = hammer_initial + np.array([0.0, -offset, 0.0])
p0 = pickup.copy()
p0[2] = clearance_z
goto_pose_arm0(p0, Q0_PICK)
p0 = translate(goto_pose_arm0, p0, pickup, Q0_PICK, step=0.01)
close_gripper_arm0()

lifted = p0.copy()
lifted[2] = clearance_z
p0 = translate(goto_pose_arm0, p0, lifted, Q0_PICK)

hammer_lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if hammer_lifted[2] - hammer_initial[2] < 0.08:
    raise RuntimeError("Pickup failed; do not carry the hammer over the gap.")

# Rotate in place above the pickup surface, never while translating.
# A -90-degree world-Z rotation points the handle toward Arm 1 (+X).
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c, s = np.cos(angle / 2.0), np.sin(angle / 2.0)
    quaternion = np.array([0.0, (c - s) / np.sqrt(2.0),
                           (c + s) / np.sqrt(2.0), 0.0])
    goto_pose_arm0(p0, quaternion)

# Use the measured handle center rather than trusting its quaternion.
hammer_rotated = np.asarray(get_hammer_pose()[0], dtype=float)
center_offset = hammer_rotated - p0
high_center = handover_center.copy()
high_center[2] = clearance_z + center_offset[2]
high_grasp = high_center - center_offset
p0 = translate(goto_pose_arm0, p0, high_grasp, Q0_PASS)

pass_grasp = handover_center - center_offset
p0 = translate(goto_pose_arm0, p0, pass_grasp, Q0_PASS, step=0.01)

for _ in range(3):
    measured = np.asarray(get_hammer_pose()[0], dtype=float)
    correction = handover_center - measured
    if np.linalg.norm(correction) < 0.003:
        break
    p0 = translate(goto_pose_arm0, p0, p0 + correction, Q0_PASS, step=0.005)

measured = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= measured[2] <= 0.20:
    raise RuntimeError("Hammer is outside the required handover height.")

receiver_grasp = measured + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receiver_grasp[:2] - p0[:2]) < 0.10:
    raise RuntimeError("Insufficient gripper clearance for handover.")

# Approach vertically on the +X handle segment, keeping Arm 0 stationary.
receiver_above = receiver_grasp.copy()
receiver_above[2] = p1[2]
p1 = translate(goto_pose_arm1, p1, receiver_above, Q1)
p1 = translate(goto_pose_arm1, p1, receiver_grasp, Q1, step=0.008)
close_gripper_arm1()

# Establish the receiving grasp before releasing the donor.
open_gripper_arm0()
retreat = p0 + np.array([0.0, 0.0, 0.15])
p0 = translate(goto_pose_arm0, p0, retreat, Q0_PASS, step=0.01)
retreat = p0 + np.array([-0.16, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat, Q0_PASS)