# Code block 0
import numpy as np

def unit(q):
    q = np.asarray(q, dtype=float)
    return q / np.linalg.norm(q)

q0_initial = unit([0, 0.707, 0.707, 0])
q1 = unit([0, 0, 1, 0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
safe_z = max(0.38, hammer[2] + 0.22)
handover_z = 0.175
midpoint_x = (0.44 + 1.18) / 2.0

open_gripper_arm1()
p1 = np.array([1.18, 0.0, safe_z + 0.10])
goto_pose_arm1(p1, q1)

open_gripper_arm0()
p0 = np.array([0.44, 0.0, safe_z])
goto_pose_arm0(p0, q0_initial)

# Grip the handle toward its head, leaving its other end available.
pickup = hammer + np.array([0.0, -0.055, 0.0])
above_pickup = pickup.copy()
above_pickup[2] = safe_z
p0 = translate(goto_pose_arm0, p0, above_pickup, q0_initial)
p0 = translate(goto_pose_arm0, p0, pickup, q0_initial, step=0.01)
close_gripper_arm0()

raised = p0.copy()
raised[2] = safe_z
p0 = translate(goto_pose_arm0, p0, raised, q0_initial, step=0.015)

# Rotate in place, above the table: handle +Y becomes +X.
# This separates the donor and receiver along their opposing approach axis.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    w, x, y, z = q0_initial
    q0 = unit([c*w - s*z, c*x - s*y, c*y + s*x, c*z + s*w])
    goto_pose_arm0(p0, q0)

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
held_offset = hammer - p0

# Transfer the hammer midpoint to the midpoint between the robots.
target_center = np.array([midpoint_x, 0.0, hammer[2]])
target_donor = target_center - held_offset
p0 = translate(goto_pose_arm0, p0, target_donor, q0)

# Lower only after the horizontal translation is complete.
target_donor = p0.copy()
target_donor[2] += handover_z - hammer[2]
p0 = translate(goto_pose_arm0, p0, target_donor, q0, step=0.01)

# Correct the actual handle-center height before bringing in the receiver.
for _ in range(3):
    hammer, _ = get_hammer_pose()
    hammer = np.asarray(hammer, dtype=float)
    error = handover_z - hammer[2]
    if abs(error) < 0.002:
        break
    corrected = p0 + np.array([0.0, 0.0, error])
    p0 = translate(goto_pose_arm0, p0, corrected, q0, step=0.005)

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
receiver = hammer + np.array([0.055, 0.0, 0.0])

# Both grip points remain on even the shortest handle, 11 cm apart.
if not (0.15 <= hammer[2] <= 0.20):
    raise RuntimeError("Hammer is outside the handover height interval.")
if np.linalg.norm(receiver - p0) < 0.09:
    raise RuntimeError("Insufficient clearance for a safe handover.")

above_receiver = receiver.copy()
above_receiver[2] = safe_z + 0.10
p1 = translate(goto_pose_arm1, p1, above_receiver, q1)
p1 = translate(goto_pose_arm1, p1, receiver, q1, step=0.01)
close_gripper_arm1()

# Release only after the receiver has closed around the handle.
open_gripper_arm0()
retreat = p0 + np.array([0.0, 0.0, 0.18])
p0 = translate(goto_pose_arm0, p0, retreat, q0, step=0.015)
retreat = p0 + np.array([-0.15, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat, q0)