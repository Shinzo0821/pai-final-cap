# Code block 0
import numpy as np

q0_pick = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q0_pass = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
safe_z = max(0.40, hammer_initial[2] + 0.22)
offset = 0.05

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * (i / count), quaternion)
    return end.copy()

open_gripper_arm1()
p1 = np.array([1.18, 0.0, safe_z])
goto_pose_arm1(p1, q1)

open_gripper_arm0()
p0 = np.array([0.44, 0.0, safe_z])
goto_pose_arm0(p0, q0_pick)

# Grasp the head-side portion of the handle, leaving its tip for Arm 1.
pickup = hammer_initial + np.array([0.0, -offset, 0.0])
above = pickup.copy()
above[2] = safe_z
p0 = translate(goto_pose_arm0, p0, above, q0_pick)
p0 = translate(goto_pose_arm0, p0, pickup, q0_pick, step=0.01)
close_gripper_arm0()

p0 = translate(goto_pose_arm0, p0, above, q0_pick)
hammer_lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if hammer_lifted[2] < hammer_initial[2] + 0.08:
    raise RuntimeError("Hammer pickup was not confirmed; aborting before the gap.")

# Rotate in place above the pickup area. The handle now points toward +X,
# so each arm approaches its own end without crossing over the other arm.
for angle in np.linspace(0.0, np.pi / 2.0, 19)[1:]:
    quaternion = np.array([
        0.0,
        np.cos(np.pi / 4.0 - angle / 2.0),
        np.sin(np.pi / 4.0 - angle / 2.0),
        0.0,
    ])
    goto_pose_arm0(p0, quaternion)

# Position the handle midpoint midway between the nominal initial grippers.
target = np.array([0.81, 0.0, 0.175])
hammer = np.asarray(get_hammer_pose()[0], dtype=float)
horizontal = p0.copy()
horizontal[:2] += target[:2] - hammer[:2]
p0 = translate(goto_pose_arm0, p0, horizontal, q0_pass)

hammer = np.asarray(get_hammer_pose()[0], dtype=float)
handover = p0 + target - hammer
p0 = translate(goto_pose_arm0, p0, handover, q0_pass, step=0.01)

hammer = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= hammer[2] <= 0.20:
    raise RuntimeError("Hammer is outside the handover height interval.")

# Both grasps lie inside even the shortest handle. Their separation is 10 cm.
receive = hammer + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receive - p0) < 0.09:
    raise RuntimeError("Insufficient gripper clearance for transfer.")

above_receive = receive.copy()
above_receive[2] = max(safe_z, receive[2] + 0.18)
p1 = translate(goto_pose_arm1, p1, above_receive, q1)
p1 = translate(goto_pose_arm1, p1, receive, q1, step=0.01)

# Establish the receiving grasp before releasing the supporting grasp.
close_gripper_arm1()
open_gripper_arm0()

retreat = p0 + np.array([0.0, 0.0, 0.16])
p0 = translate(goto_pose_arm0, p0, retreat, q0_pass, step=0.01)
retreat = p0 + np.array([-0.18, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat, q0_pass)