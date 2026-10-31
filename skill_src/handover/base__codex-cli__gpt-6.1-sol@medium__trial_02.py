# Code block 0
import numpy as np

q0_initial = np.array([0.0, 1.0, 1.0, 0.0])
q0_initial /= np.linalg.norm(q0_initial)
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, target, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    target = np.asarray(target, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(target - start) / step)))
    for i in range(1, count + 1):
        move(start + (target - start) * (i / count), quaternion)
    return target.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

# Use two handle grasp sites 10 cm apart, both inside the shortest handle.
offset = 0.05
travel_z = max(0.36, hammer[2] + 0.22)
handover_center = np.array([0.81, 0.0, 0.175])

open_gripper_arm1()
p1 = np.array([1.18, 0.0, travel_z])
goto_pose_arm1(p1, q1)

open_gripper_arm0()
pickup = hammer + np.array([0.0, -offset, 0.0])
p0 = pickup.copy()
p0[2] = travel_z
goto_pose_arm0(p0, q0_initial, z_approach=0.08)
p0 = translate(goto_pose_arm0, p0, pickup, q0_initial)
close_gripper_arm0()

raised = p0.copy()
raised[2] = travel_z
p0 = translate(goto_pose_arm0, p0, raised, q0_initial)

# Rotate in place, clear of the table: the free handle end now faces Arm 1.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c, s = np.cos(angle / 2.0), np.sin(angle / 2.0)
    q0 = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(p0, q0)

# Use measured handle-center position to preserve the actual grasp offset.
measured, _ = get_hammer_pose()
grasp_offset0 = p0 - np.asarray(measured, dtype=float)
high_center = handover_center.copy()
high_center[2] = travel_z
p0 = translate(goto_pose_arm0, p0, high_center + grasp_offset0, q0)
p0 = translate(goto_pose_arm0, p0, handover_center + grasp_offset0, q0)

# Correct the object height before bringing the receiving gripper close.
for _ in range(3):
    measured, _ = get_hammer_pose()
    measured = np.asarray(measured, dtype=float)
    correction = handover_center - measured
    if np.linalg.norm(correction) < 0.002:
        break
    p0 = translate(goto_pose_arm0, p0, p0 + correction, q0)

measured, _ = get_hammer_pose()
measured = np.asarray(measured, dtype=float)
if not 0.15 <= measured[2] <= 0.20:
    raise RuntimeError("Hammer is outside the required handover height.")

receive = measured + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receive - p0) < 0.09:
    raise RuntimeError("Insufficient gripper separation for handover.")

# Approach vertically at the free handle segment, keeping the arms separated.
above_receive = receive.copy()
above_receive[2] = travel_z + 0.08
p1 = translate(goto_pose_arm1, p1, above_receive, q1)
p1 = translate(goto_pose_arm1, p1, receive, q1)
close_gripper_arm1()

# Never release over the gap until the receiving gripper has closed.
open_gripper_arm0()
retreat = p0 + np.array([-0.14, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat, q0)
raised_retreat = p0.copy()
raised_retreat[2] = travel_z
p0 = translate(goto_pose_arm0, p0, raised_retreat, q0)