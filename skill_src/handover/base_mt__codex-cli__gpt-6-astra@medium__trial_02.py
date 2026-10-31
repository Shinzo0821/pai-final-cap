# Code block 0
import numpy as np

q0_pick = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q0_offer = np.array([0.0, 1.0, 0.0, 0.0])
q1_take = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
safe_z = max(0.38, hammer[2] + 0.22)

# Reserve the receiver's side before moving the hammer into the gap.
open_gripper_arm1()
receiver = np.array([1.18, 0.0, safe_z])
goto_pose_arm1(receiver, q1_take)

# Both grasp points fit even the shortest handle, with 11 cm separation.
offset = 0.055
pickup = hammer + np.array([0.0, -offset, 0.0])
open_gripper_arm0()
donor = pickup.copy()
donor[2] = safe_z
goto_pose_arm0(donor, q0_pick)
donor = translate(goto_pose_arm0, donor, pickup, q0_pick)
close_gripper_arm0()

lifted = donor.copy()
lifted[2] = safe_z
donor = translate(goto_pose_arm0, donor, lifted, q0_pick)

raised_hammer, _ = get_hammer_pose()
if raised_hammer[2] < hammer[2] + 0.08:
    raise RuntimeError("Hammer pickup failed; do not enter the central gap.")

# Rotate in place above the pickup area, separately from translation.
# Clockwise yaw puts the head toward Arm 0 and the free handle toward Arm 1.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    half = np.pi / 4.0 + angle / 2.0
    quaternion = np.array([0.0, np.cos(half), np.sin(half), 0.0])
    goto_pose_arm0(donor, quaternion)

current_hammer, _ = get_hammer_pose()
current_hammer = np.asarray(current_hammer, dtype=float)
target_hammer = np.array([0.81, 0.0, 0.175])
target_donor = donor + target_hammer - current_hammer

over_handover = target_donor.copy()
over_handover[2] = safe_z
donor = translate(goto_pose_arm0, donor, over_handover, q0_offer)
donor = translate(goto_pose_arm0, donor, target_donor, q0_offer)

# Correct actual handle-center height before bringing the receiver close.
for _ in range(3):
    actual, _ = get_hammer_pose()
    error = target_hammer - np.asarray(actual, dtype=float)
    if np.linalg.norm(error) < 0.003:
        break
    donor = translate(goto_pose_arm0, donor, donor + error, q0_offer)

actual, _ = get_hammer_pose()
actual = np.asarray(actual, dtype=float)
if not 0.15 <= actual[2] <= 0.20:
    raise RuntimeError("Handover height is outside the permitted interval.")

receive_point = actual + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receive_point - donor) < 0.08:
    raise RuntimeError("Insufficient gripper clearance.")

# Approach vertically at the free handle end; never release over the gap
# until the receiver has closed.
receive_above = receive_point.copy()
receive_above[2] = safe_z
receiver = translate(goto_pose_arm1, receiver, receive_above, q1_take)
receiver = translate(goto_pose_arm1, receiver, receive_point, q1_take)
close_gripper_arm1()
open_gripper_arm0()

retreat = donor.copy()
retreat[2] = safe_z
donor = translate(goto_pose_arm0, donor, retreat, q0_offer)