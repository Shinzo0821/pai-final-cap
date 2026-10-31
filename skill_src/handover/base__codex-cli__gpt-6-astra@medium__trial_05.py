# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1_transfer = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
clearance = max(0.35, hammer[2] + 0.20)

# Reserve the central workspace for Arm 0 until the hammer is positioned.
open_gripper_arm1()
p1 = np.array([1.18, 0.0, clearance + 0.10])
goto_pose_arm1(p1, q1_transfer)

# Both grasp sites remain on even the shortest handle, 11 cm apart.
offset = 0.055
pick = hammer + np.array([0.0, -offset, 0.0])
open_gripper_arm0()
p0 = np.array([pick[0], pick[1], clearance])
goto_pose_arm0(p0, q0_pick)
p0 = translate(goto_pose_arm0, p0, pick, q0_pick)
close_gripper_arm0()

raised = p0.copy()
raised[2] = clearance
p0 = translate(goto_pose_arm0, p0, raised, q0_pick)

# Rotate in place above the table: the handle's +Y direction becomes +X.
# Arm 0 retains the head-side handle segment; Arm 1 takes the free end.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    q = np.array([0.0, (c - s) / np.sqrt(2.0),
                  (c + s) / np.sqrt(2.0), 0.0])
    goto_pose_arm0(p0, q)

# Use measured handle-center position rather than the unreliable quaternion.
center, _ = get_hammer_pose()
center = np.asarray(center, dtype=float)
target_center = np.array([0.81, 0.0, 0.175])
destination = p0 + target_center - center

horizontal = destination.copy()
horizontal[2] = p0[2]
p0 = translate(goto_pose_arm0, p0, horizontal, q0_transfer)
p0 = translate(goto_pose_arm0, p0, destination, q0_transfer)

center, _ = get_hammer_pose()
center = np.asarray(center, dtype=float)
if not 0.15 <= center[2] <= 0.20:
    correction = p0.copy()
    correction[2] += 0.175 - center[2]
    p0 = translate(goto_pose_arm0, p0, correction, q0_transfer)
    center, _ = get_hammer_pose()
    center = np.asarray(center, dtype=float)

receive = center + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receive - p0) < 0.08:
    raise RuntimeError("Insufficient gripper clearance; retaining hammer in Arm 0.")

# Approach vertically with fixed orientation and separated grasp sites.
above_receive = receive.copy()
above_receive[2] = p1[2]
p1 = translate(goto_pose_arm1, p1, above_receive, q1_transfer)
p1 = translate(goto_pose_arm1, p1, receive, q1_transfer)
close_gripper_arm1()

# Never release over the gap until the receiving gripper has closed.
open_gripper_arm0()
retreat = p0 + np.array([-0.12, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat, q0_transfer)
retreat = p0.copy()
retreat[2] = clearance
p0 = translate(goto_pose_arm0, p0, retreat, q0_transfer)