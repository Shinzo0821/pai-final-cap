# Code block 0
import numpy as np

q0_initial = np.array([0.0, 1.0, 1.0, 0.0])
q0_initial /= np.linalg.norm(q0_initial)
q_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
safe_z = max(0.42, hammer[2] + 0.22)
midpoint_x = (0.44 + 1.18) / 2.0

open_gripper_arm0()
open_gripper_arm1()

# Keep the receiving arm well outside the pickup and rotation region.
receiver = np.array([1.18, 0.0, safe_z])
goto_pose_arm1(receiver, q1)

# Grasp the head-side portion of the handle, leaving its far end available.
pickup = hammer + np.array([0.0, -0.05, 0.0])
giver = pickup.copy()
giver[2] = safe_z
goto_pose_arm0(giver, q0_initial)
giver = translate(goto_pose_arm0, giver, pickup, q0_initial)
close_gripper_arm0()

raised = giver.copy()
raised[2] = safe_z
giver = translate(goto_pose_arm0, giver, raised, q0_initial)

# Rotate in place: the handle now points toward Arm 1 along +X.
# The two eventual grasp sites are 10 cm apart.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    q = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(giver, q)

handover_center = np.array([midpoint_x, 0.0, 0.175])
overhead_center = handover_center.copy()
overhead_center[2] = safe_z

# Use measured handle position rather than assuming an exact grasp offset.
actual, _ = get_hammer_pose()
target = giver + overhead_center - np.asarray(actual)
giver = translate(goto_pose_arm0, giver, target, q_transfer)

actual, _ = get_hammer_pose()
target = giver + handover_center - np.asarray(actual)
giver = translate(goto_pose_arm0, giver, target, q_transfer)

actual, _ = get_hammer_pose()
actual = np.asarray(actual, dtype=float)
if not 0.15 <= actual[2] <= 0.20:
    target = giver + np.array([0.0, 0.0, 0.175 - actual[2]])
    giver = translate(goto_pose_arm0, giver, target, q_transfer)
    actual, _ = get_hammer_pose()
    actual = np.asarray(actual, dtype=float)

receive_grasp = actual + np.array([0.05, 0.0, 0.0])

# Descend away from Arm 0, then approach along the handle from its free end.
staging = receive_grasp + np.array([0.16, 0.0, 0.0])
staging_high = staging.copy()
staging_high[2] = safe_z
receiver = translate(goto_pose_arm1, receiver, staging_high, q1)
receiver = translate(goto_pose_arm1, receiver, staging, q1)
receiver = translate(goto_pose_arm1, receiver, receive_grasp, q1)
close_gripper_arm1()

# Never release over the gap until the receiving gripper has closed.
open_gripper_arm0()
retreat = giver + np.array([0.0, 0.0, 0.18])
giver = translate(goto_pose_arm0, giver, retreat, q_transfer)
retreat = giver + np.array([-0.15, 0.0, 0.0])
giver = translate(goto_pose_arm0, giver, retreat, q_transfer)