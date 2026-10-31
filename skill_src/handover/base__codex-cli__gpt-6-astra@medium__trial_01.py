# Code block 0
import numpy as np

q0_pick = np.array([0.0, 2**-0.5, 2**-0.5, 0.0])
q0_pass = np.array([0.0, 1.0, 0.0, 0.0])
q1_pass = np.array([0.0, 0.0, 1.0, 0.0])

hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
safe_z = max(0.40, hammer_initial[2] + 0.22)
offset = 0.055
positions = {}
orientations = {}


def initialize(arm, position, quaternion):
    move = goto_pose_arm0 if arm == 0 else goto_pose_arm1
    move(np.asarray(position, dtype=float), quaternion)
    positions[arm] = np.asarray(position, dtype=float).copy()
    orientations[arm] = quaternion.copy()


def translate(arm, target):
    move = goto_pose_arm0 if arm == 0 else goto_pose_arm1
    start = positions[arm].copy()
    target = np.asarray(target, dtype=float)
    steps = max(1, int(np.ceil(np.linalg.norm(target - start) / 0.02)))
    for fraction in np.linspace(0.0, 1.0, steps + 1)[1:]:
        waypoint = start + fraction * (target - start)
        other = positions.get(1 - arm)
        if other is not None and np.linalg.norm(waypoint - other) < 0.10:
            raise RuntimeError("Insufficient gripper clearance; retaining current grasp.")
        move(waypoint, orientations[arm])
        positions[arm] = waypoint.copy()


# Park the receiving arm outside the transfer corridor.
initialize(1, [1.18, 0.0, safe_z + 0.10], q1_pass)
open_gripper_arm1()
initialize(0, [0.44, 0.0, safe_z], q0_pick)
open_gripper_arm0()

# Both grasp sites fit within even the shortest handle.
# Arm 0 holds the head-side handle segment, leaving the tip-side segment free.
pick = hammer_initial + np.array([0.0, -offset, 0.0])
translate(0, [pick[0], pick[1], safe_z])
translate(0, pick)
close_gripper_arm0()
translate(0, [pick[0], pick[1], safe_z])

lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if lifted[2] < hammer_initial[2] + 0.08:
    raise RuntimeError("Hammer did not lift; refusing to cross the table gap.")

# Rotate in place at clearance height: +Y handle direction becomes +X.
# This leaves the head toward Arm 0 and the free handle toward Arm 1.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c, s = np.cos(angle / 2.0), np.sin(angle / 2.0)
    quaternion = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(positions[0], quaternion)
    orientations[0] = quaternion
orientations[0] = q0_pass.copy()

# Use measured handle-center position rather than assuming a perfect grasp.
center = np.asarray(get_hammer_pose()[0], dtype=float)
target_center = np.array([0.81, 0.0, 0.175])
destination = positions[0] + target_center - center
translate(0, [destination[0], destination[1], positions[0][2]])
translate(0, destination)

center = np.asarray(get_hammer_pose()[0], dtype=float)
if np.linalg.norm(center - target_center) > 0.005:
    translate(0, positions[0] + target_center - center)

center = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= center[2] <= 0.20:
    raise RuntimeError("Hammer outside handover height; retaining Arm 0 grasp.")

receiver = center + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receiver - positions[0]) < 0.10:
    raise RuntimeError("Unsafe transfer spacing; retaining Arm 0 grasp.")

# Approach from above without sweeping the receiver across the donor.
translate(1, [receiver[0], receiver[1], safe_z + 0.10])
translate(1, receiver)
close_gripper_arm1()

# Establish the receiving grasp before releasing the donor over the gap.
open_gripper_arm0()
translate(0, positions[0] + np.array([0.0, 0.0, 0.15]))
translate(0, [0.44, positions[0][1], positions[0][2]])