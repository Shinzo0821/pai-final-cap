# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1_transfer = np.array([0.0, 0.0, 1.0, 0.0])

hammer_start = np.asarray(get_hammer_pose()[0], dtype=float).copy()
safe_z = max(0.40, hammer_start[2] + 0.22)
midpoint = np.array([0.81, 0.0, 0.175])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

# Keep the receiving arm on its own side, above the transfer plane.
open_gripper_arm1()
receiver_park = np.array([1.18, 0.0, safe_z + 0.12])
goto_pose_arm1(receiver_park, q1_transfer)

# Grip the headward portion of the handle, leaving its other end free.
open_gripper_arm0()
pickup = hammer_start + np.array([0.0, -0.05, 0.0])
p0 = pickup + np.array([0.0, 0.0, safe_z - pickup[2]])
goto_pose_arm0(p0, q0_pick)
p0 = translate(goto_pose_arm0, p0, pickup, q0_pick)
close_gripper_arm0()

p0 = translate(
    goto_pose_arm0, p0,
    np.array([p0[0], p0[1], safe_z]), q0_pick
)
hammer_lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if hammer_lifted[2] < hammer_start[2] + 0.08:
    raise RuntimeError("Hammer pickup failed; do not cross the table gap.")

# Rotate in place above the pickup area before translating.
# A -90 degree world-Z rotation puts the handle tip toward Arm 1 (+X).
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c, s = np.cos(angle / 2.0), np.sin(angle / 2.0)
    q = np.array([0.0, (c - s) / np.sqrt(2.0),
                  (c + s) / np.sqrt(2.0), 0.0])
    goto_pose_arm0(p0, q)

# Use the measured handle center rather than the unreliable object quaternion.
hammer_now = np.asarray(get_hammer_pose()[0], dtype=float)
grip_offset = p0 - hammer_now
hammer_high = midpoint.copy()
hammer_high[2] = max(safe_z, hammer_now[2])
target0_high = hammer_high + grip_offset

p0 = translate(
    goto_pose_arm0, p0,
    np.array([p0[0], p0[1], target0_high[2]]), q0_transfer
)
p0 = translate(goto_pose_arm0, p0, target0_high, q0_transfer)
p0 = translate(
    goto_pose_arm0, p0, midpoint + grip_offset, q0_transfer
)

# Correct small placement errors while Arm 1 remains parked.
for _ in range(3):
    hammer_now = np.asarray(get_hammer_pose()[0], dtype=float)
    error = midpoint - hammer_now
    if np.linalg.norm(error) < 0.003:
        break
    if np.linalg.norm(error) > 0.06:
        raise RuntimeError("Hammer slipped; halt without releasing.")
    p0 = translate(goto_pose_arm0, p0, p0 + error, q0_transfer)

hammer_now = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 < hammer_now[2] < 0.20:
    raise RuntimeError("Hammer is outside the handover height window.")

# Both grasp sites lie within even the shortest handle and are 10 cm apart.
receiver_grasp = hammer_now + np.array([0.05, 0.0, 0.0])
if np.linalg.norm(receiver_grasp[:2] - p0[:2]) < 0.09:
    raise RuntimeError("Insufficient gripper clearance.")

receiver_above = receiver_grasp.copy()
receiver_above[2] = receiver_park[2]
p1 = translate(
    goto_pose_arm1, receiver_park, receiver_above, q1_transfer
)
p1 = translate(goto_pose_arm1, p1, receiver_grasp, q1_transfer)
close_gripper_arm1()

# Establish the receiving grasp before releasing over the central gap.
open_gripper_arm0()
p0 = translate(
    goto_pose_arm0, p0, p0 + np.array([0.0, 0.0, 0.16]),
    q0_transfer
)
p0 = translate(
    goto_pose_arm0, p0, p0 + np.array([-0.18, 0.0, 0.0]),
    q0_transfer
)
# Arm 1 remains closed, holding the handle at the required handover height.