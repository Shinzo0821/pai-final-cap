# Code block 0
import numpy as np

q0 = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    steps = max(1, int(np.ceil(np.linalg.norm(end - start) / 0.02)))
    for fraction in np.linspace(0.0, 1.0, steps + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer_initial, _ = get_hammer_pose()
hammer_initial = np.asarray(hammer_initial, dtype=float)
clearance = max(0.35, hammer_initial[2] + 0.20)

# Park the receiving arm on its own side before approaching the hammer.
open_gripper_arm1()
receiver = np.array([1.18, 0.0, clearance])
goto_pose_arm1(receiver, q1)

# Both grasp points lie on even the shortest handle, 10 cm apart.
open_gripper_arm0()
pickup = hammer_initial + np.array([0.0, -0.05, 0.0])
donor = pickup.copy()
donor[2] = clearance
goto_pose_arm0(donor, q0)
donor = translate(goto_pose_arm0, donor, pickup, q0)
close_gripper_arm0()

lifted = donor.copy()
lifted[2] = clearance
donor = translate(goto_pose_arm0, donor, lifted, q0)

hammer_lifted, _ = get_hammer_pose()
if np.asarray(hammer_lifted)[2] < hammer_initial[2] + 0.08:
    raise RuntimeError("Hammer did not lift; aborting before entering the gap.")

# Rotate in place above the table: the handle now extends toward Arm 1 (+X).
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c, s = np.cos(angle / 2.0), np.sin(angle / 2.0)
    quaternion = np.array([0.0, (c - s) / np.sqrt(2.0),
                           (c + s) / np.sqrt(2.0), 0.0])
    goto_pose_arm0(donor, quaternion)

# Use the measured handle center rather than the unreliable object quaternion.
hammer_rotated, _ = get_hammer_pose()
offset = np.asarray(hammer_rotated, dtype=float) - donor
target_center = np.array([0.81, 0.0, 0.175])
handover_donor = target_center - offset

high_target = handover_donor.copy()
high_target[2] = clearance
donor = translate(goto_pose_arm0, donor, high_target, q_transfer)
donor = translate(goto_pose_arm0, donor, handover_donor, q_transfer)

hammer_now, _ = get_hammer_pose()
hammer_now = np.asarray(hammer_now, dtype=float)
if not 0.15 <= hammer_now[2] <= 0.20:
    raise RuntimeError("Hammer is outside the required handover height.")

receiver_grasp = hammer_now + np.array([0.05, 0.0, 0.0])
if np.linalg.norm(receiver_grasp - donor) < 0.08:
    raise RuntimeError("Insufficient gripper separation for handover.")

# Approach vertically, preserving separation from the donor throughout.
receiver_above = receiver_grasp.copy()
receiver_above[2] = clearance
receiver = translate(goto_pose_arm1, receiver, receiver_above, q1)
receiver = translate(goto_pose_arm1, receiver, receiver_grasp, q1)

# Establish the receiving grasp before releasing the donor.
close_gripper_arm1()
open_gripper_arm0()

retreat = donor.copy()
retreat[2] = clearance
donor = translate(goto_pose_arm0, donor, retreat, q_transfer)
retreat = donor.copy()
retreat[0] = 0.44
translate(goto_pose_arm0, donor, retreat, q_transfer)