# Code block 0
import numpy as np

q0_initial = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
safe_z = max(0.36, hammer[2] + 0.22)
transfer_center = np.array([0.81, 0.0, 0.175])

def translate(go, start, target, quaternion):
    start = np.asarray(start, dtype=float)
    target = np.asarray(target, dtype=float)
    steps = max(1, int(np.ceil(np.linalg.norm(target - start) / 0.02)))
    for i in range(1, steps + 1):
        go(start + (target - start) * (i / steps), quaternion)
    return target.copy()

# Keep the receiving arm outside the pickup and rotation workspace.
open_gripper_arm1()
p1 = np.array([1.18, 0.0, safe_z])
goto_pose_arm1(p1, q1)

# Grasp the headward portion of the handle, leaving its tip for Arm 1.
open_gripper_arm0()
pickup = hammer + np.array([0.0, -0.05, 0.0])
p0 = pickup.copy()
p0[2] = safe_z
goto_pose_arm0(p0, q0_initial)
p0 = translate(goto_pose_arm0, p0, pickup, q0_initial)
close_gripper_arm0()

raised = p0.copy()
raised[2] = safe_z
p0 = translate(goto_pose_arm0, p0, raised, q0_initial)

# Rotate in place above the table: the handle now points toward +X.
# This leaves the hammer head toward Arm 0 and the free handle toward Arm 1.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    q = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(p0, q)

# Use observed handle position rather than relying on an exact grasp offset.
observed, _ = get_hammer_pose()
observed = np.asarray(observed, dtype=float)
raised_center = transfer_center.copy()
raised_center[2] = safe_z
target0 = p0 + raised_center - observed
p0 = translate(goto_pose_arm0, p0, target0, q0_transfer)

observed, _ = get_hammer_pose()
observed = np.asarray(observed, dtype=float)
target0 = p0 + transfer_center - observed
p0 = translate(goto_pose_arm0, p0, target0, q0_transfer)

# Arm 1 approaches vertically at the tipward handle segment.
# Nominal simultaneous grasp separation is 10.5 cm.
observed, _ = get_hammer_pose()
observed = np.asarray(observed, dtype=float)
receive = observed + np.array([0.055, 0.0, 0.0])
above_receive = receive.copy()
above_receive[2] = safe_z
p1 = translate(goto_pose_arm1, p1, above_receive, q1)

if np.linalg.norm(receive - p0) < 0.08:
    raise RuntimeError("Insufficient gripper clearance; retaining Arm 0 grasp.")
if not 0.15 <= observed[2] <= 0.20:
    raise RuntimeError("Hammer outside handover height; retaining Arm 0 grasp.")

p1 = translate(goto_pose_arm1, p1, receive, q1)
close_gripper_arm1()
open_gripper_arm0()

# Clear the donor vertically before moving either arm laterally.
clear0 = p0 + np.array([0.0, 0.0, 0.16])
p0 = translate(goto_pose_arm0, p0, clear0, q0_transfer)
retreat0 = p0 + np.array([-0.18, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat0, q0_transfer)