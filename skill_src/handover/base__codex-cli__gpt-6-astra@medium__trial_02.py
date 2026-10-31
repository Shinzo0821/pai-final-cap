# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
clearance_z = max(0.40, hammer_initial[2] + 0.22)

# Keep the receiving arm away while the donor picks and rotates.
open_gripper_arm1()
receiver = np.array([1.18, 0.0, clearance_z + 0.12])
goto_pose_arm1(receiver, q1)

# Grip toward the head, leaving the opposite handle segment accessible.
open_gripper_arm0()
pickup = hammer_initial + np.array([0.0, -0.05, 0.0])
donor = pickup.copy()
donor[2] = clearance_z
goto_pose_arm0(donor, q0_pick)
donor = translate(goto_pose_arm0, donor, pickup, q0_pick)

close_gripper_arm0()
raised = donor.copy()
raised[2] = clearance_z
donor = translate(goto_pose_arm0, donor, raised, q0_pick)

hammer_raised = np.asarray(get_hammer_pose()[0], dtype=float)
if hammer_raised[2] < hammer_initial[2] + 0.08:
    raise RuntimeError("Hammer did not lift; refusing to cross the central gap.")

# Rotate in place above the pickup area: handle +Y becomes +X.
# Both arms can then approach their own side of the handle.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    half_angle = np.pi / 4.0 + angle / 2.0
    quaternion = np.array(
        [0.0, np.cos(half_angle), np.sin(half_angle), 0.0]
    )
    goto_pose_arm0(donor, quaternion)

# Translate separately from rotation, using the measured handle midpoint.
handover = np.array([0.81, 0.0, 0.175])
hammer = np.asarray(get_hammer_pose()[0], dtype=float)
destination = donor.copy()
destination[:2] += handover[:2] - hammer[:2]
donor = translate(goto_pose_arm0, donor, destination, q0_transfer)

hammer = np.asarray(get_hammer_pose()[0], dtype=float)
destination = donor.copy()
destination[2] += handover[2] - hammer[2]
donor = translate(goto_pose_arm0, donor, destination, q0_transfer)

# Correct small positioning errors before the receiving arm approaches.
for _ in range(3):
    hammer = np.asarray(get_hammer_pose()[0], dtype=float)
    error = handover - hammer
    if np.linalg.norm(error) < 0.003:
        break
    donor = translate(goto_pose_arm0, donor, donor + error, q0_transfer)

hammer = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= hammer[2] <= 0.20:
    raise RuntimeError("Hammer is outside the permitted handover height.")

# Two grasp sites are 10 cm apart, both within the shortest handle.
receiver_grasp = hammer + np.array([0.05, 0.0, 0.0])
if np.linalg.norm(receiver_grasp[:2] - donor[:2]) < 0.09:
    raise RuntimeError("Insufficient gripper separation for a safe transfer.")

receiver_above = receiver_grasp.copy()
receiver_above[2] = receiver[2]
receiver = translate(goto_pose_arm1, receiver, receiver_above, q1)
receiver = translate(goto_pose_arm1, receiver, receiver_grasp, q1)

# Never release the donor until the receiver has closed on the handle.
close_gripper_arm1()
open_gripper_arm0()

# Withdraw vertically before moving back toward Arm 0's side.
donor_above = donor + np.array([0.0, 0.0, 0.18])
donor = translate(goto_pose_arm0, donor, donor_above, q0_transfer)
donor_home = donor.copy()
donor_home[0] = 0.44
donor = translate(goto_pose_arm0, donor, donor_home, q0_transfer)