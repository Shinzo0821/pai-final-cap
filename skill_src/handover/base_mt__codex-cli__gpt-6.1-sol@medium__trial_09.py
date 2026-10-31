# Code block 0
import numpy as np

q0 = np.array([0.0, 1.0, 1.0, 0.0])
q0 /= np.linalg.norm(q0)
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.015):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quaternion)
    return end.copy()

def rotate_about_z(quaternion, angle):
    w, x, y, z = quaternion
    c, s = np.cos(angle / 2), np.sin(angle / 2)
    return np.array([c*w - s*z, c*x - s*y, c*y + s*x, c*z + s*w])

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

# Keep the receiving arm out of the pickup and transport corridor.
open_gripper_arm1()
park1 = np.array([1.18, 0.0, max(0.38, hammer[2] + 0.22)])
goto_pose_arm1(park1, q1)

# Both grasp points lie on even the shortest handle, 11 cm apart.
offset = 0.055
pickup = hammer + np.array([0.0, -offset, 0.0])
above = pickup + np.array([0.0, 0.0, 0.16])

open_gripper_arm0()
goto_pose_arm0(above, q0)
p0 = translate(goto_pose_arm0, above, pickup, q0)
close_gripper_arm0()

# Lift vertically before rotating or transporting the hammer.
lifted = p0.copy()
lifted[2] += max(0.16, 0.34 - hammer[2])
p0 = translate(goto_pose_arm0, p0, lifted, q0)

# Rotate in place: the handle points toward +X, toward Arm 1.
# Arm 0 holds its -X end; Arm 1 will receive its +X end.
for angle in np.linspace(0.0, -np.pi / 2, 19)[1:]:
    q = rotate_about_z(q0, angle)
    goto_pose_arm0(p0, q)
q0 = q.copy()

# Use measured handle-center position rather than the unreliable quaternion.
hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
handover_center = np.array([(0.44 + 1.18) / 2, 0.0, 0.175])

transport_center = handover_center.copy()
transport_center[2] = max(0.34, hammer[2])
destination = p0 + transport_center - hammer
p0 = translate(goto_pose_arm0, p0, destination, q0)

# Descend only after reaching the central handover location.
hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
destination = p0 + handover_center - hammer
p0 = translate(goto_pose_arm0, p0, destination, q0)

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
if not 0.15 <= hammer[2] <= 0.20:
    raise RuntimeError("Hammer is outside the handover height window.")

receive = hammer + np.array([offset, 0.0, 0.0])
hover = receive + np.array([0.0, 0.0, 0.18])

# Approach from Arm 1's side, then descend without rotating near Arm 0.
outer = np.array([park1[0], hover[1], park1[2]])
p1 = translate(goto_pose_arm1, park1, outer, q1)
outer[2] = hover[2]
p1 = translate(goto_pose_arm1, p1, outer, q1)
p1 = translate(goto_pose_arm1, p1, hover, q1)

if np.linalg.norm((receive - p0)[:2]) < 0.095:
    raise RuntimeError("Insufficient clearance for the receiving gripper.")

p1 = translate(goto_pose_arm1, p1, receive, q1, step=0.005)
close_gripper_arm1()

# Maintain overlapping support across the gap; release only after closing Arm 1.
open_gripper_arm0()

# Withdraw away from Arm 1 before any upward motion.
retreat = p0 + np.array([-0.14, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat, q0)
retreat[2] += 0.16
p0 = translate(goto_pose_arm0, p0, retreat, q0)