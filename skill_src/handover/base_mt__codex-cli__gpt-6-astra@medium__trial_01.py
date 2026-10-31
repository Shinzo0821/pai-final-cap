# Code block 0
import numpy as np

q0_initial = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
clearance_z = max(0.40, hammer_initial[2] + 0.25)

# Use opposite ends of the shortest possible handle, leaving 11 cm
# between grippers. Arm 0 grips the headward part of the handle.
offset = 0.055
pickup = hammer_initial + np.array([0.0, -offset, 0.0])

open_gripper_arm1()
p1 = np.array([1.18, 0.0, clearance_z])
goto_pose_arm1(p1, q1)

open_gripper_arm0()
p0 = pickup.copy()
p0[2] = clearance_z
goto_pose_arm0(p0, q0_initial)
p0 = translate(goto_pose_arm0, p0, pickup, q0_initial)
close_gripper_arm0()

lifted = p0.copy()
lifted[2] = clearance_z
p0 = translate(goto_pose_arm0, p0, lifted, q0_initial)

hammer_lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if hammer_lifted[2] < hammer_initial[2] + 0.08:
    raise RuntimeError("Hammer did not lift; refusing to move over the gap.")

# Rotate in place while still over the pickup side. A clockwise quarter
# turn puts the handle toward Arm 1 (+X), with the head toward Arm 0.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    quaternion = np.array([
        0.0,
        np.cos(np.pi / 4.0 + angle / 2.0),
        np.sin(np.pi / 4.0 + angle / 2.0),
        0.0,
    ])
    goto_pose_arm0(p0, quaternion)

# Center the hammer near the midpoint of the initial gripper positions.
hammer_now = np.asarray(get_hammer_pose()[0], dtype=float)
hammer_target = np.array([0.81, 0.0, 0.175])
gripper_target = p0 + hammer_target - hammer_now

across = gripper_target.copy()
across[2] = p0[2]
p0 = translate(goto_pose_arm0, p0, across, q0_transfer)
p0 = translate(goto_pose_arm0, p0, gripper_target, q0_transfer)

# Correct small placement errors using the measured handle midpoint.
for _ in range(3):
    hammer_now = np.asarray(get_hammer_pose()[0], dtype=float)
    error = hammer_target - hammer_now
    if np.linalg.norm(error) < 0.003:
        break
    p0 = translate(goto_pose_arm0, p0, p0 + error, q0_transfer)

hammer_now = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= hammer_now[2] <= 0.20:
    raise RuntimeError("Hammer is outside the handover height band.")

receiver = hammer_now + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receiver[:2] - p0[:2]) < 0.08:
    raise RuntimeError("Insufficient gripper separation.")

# Approach vertically at the exposed handle end, never crossing Arm 0.
receiver_above = receiver.copy()
receiver_above[2] = clearance_z
p1 = translate(goto_pose_arm1, p1, receiver_above, q1)
p1 = translate(goto_pose_arm1, p1, receiver, q1)
close_gripper_arm1()

# Establish the receiving grasp before releasing the supporting grasp.
open_gripper_arm0()
retreat0 = p0 + np.array([0.0, 0.0, 0.15])
p0 = translate(goto_pose_arm0, p0, retreat0, q0_transfer)
retreat0 = p0 + np.array([-0.15, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat0, q0_transfer)