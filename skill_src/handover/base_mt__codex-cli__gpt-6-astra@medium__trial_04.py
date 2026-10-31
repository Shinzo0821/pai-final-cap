# Code block 0
import numpy as np

q0 = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
midpoint = np.array([0.81, 0.0, 0.175])
safe_z = max(0.35, hammer[2] + 0.22)

def translate(move, start, end, quaternion):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    steps = max(1, int(np.ceil(np.linalg.norm(end - start) / 0.025)))
    for fraction in np.linspace(0.0, 1.0, steps + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

# Keep the receiving arm away while picking up and rotating the hammer.
open_gripper_arm1()
receiver = np.array([1.18, 0.0, safe_z + 0.12])
goto_pose_arm1(receiver, q1)

# Both grasp sites lie inside even the shortest handle, 10 cm apart.
open_gripper_arm0()
pickup = hammer + np.array([0.0, -0.05, 0.0])
giver = pickup.copy()
giver[2] = safe_z
goto_pose_arm0(giver, q0)
giver = translate(goto_pose_arm0, giver, pickup, q0)
close_gripper_arm0()

lifted = giver.copy()
lifted[2] = safe_z
giver = translate(goto_pose_arm0, giver, lifted, q0)

# Rotate in place above the table: the handle now extends toward Arm 1
# along +X, with the head on Arm 0's side.
for angle in np.linspace(0.0, -np.pi / 2.0, 13)[1:]:
    c, s = np.cos(angle / 2.0), np.sin(angle / 2.0)
    quaternion = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(giver, quaternion)

# Use measured handle-center position rather than the unreliable quaternion.
center, _ = get_hammer_pose()
high_center = midpoint.copy()
high_center[2] = safe_z
destination = giver + high_center - np.asarray(center)
giver = translate(goto_pose_arm0, giver, destination, q_transfer)

center, _ = get_hammer_pose()
destination = giver + midpoint - np.asarray(center)
giver = translate(goto_pose_arm0, giver, destination, q_transfer)

center, _ = get_hammer_pose()
center = np.asarray(center, dtype=float)
if not 0.15 <= center[2] <= 0.20:
    raise RuntimeError("Hammer is outside the required handover height.")

receive = center + np.array([0.05, 0.0, 0.0])
if np.linalg.norm(receive - giver) < 0.08:
    raise RuntimeError("Insufficient gripper separation for handover.")

# Approach vertically at the far handle site, maintaining 10 cm separation.
above_receive = receive.copy()
above_receive[2] = safe_z + 0.12
receiver = translate(goto_pose_arm1, receiver, above_receive, q1)
receiver = translate(goto_pose_arm1, receiver, receive, q1)

# Never release the giver before the receiver has closed.
close_gripper_arm1()
open_gripper_arm0()

retreat = giver + np.array([0.0, 0.0, 0.15])
giver = translate(goto_pose_arm0, giver, retreat, q_transfer)
retreat = giver + np.array([-0.15, 0.0, 0.0])
giver = translate(goto_pose_arm0, giver, retreat, q_transfer)