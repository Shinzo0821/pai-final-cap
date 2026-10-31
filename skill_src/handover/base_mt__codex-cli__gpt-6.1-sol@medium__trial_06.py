# Code block 0
import numpy as np

def unit(q):
    q = np.asarray(q, dtype=float)
    return q / np.linalg.norm(q)

def translate(move, start, end, q, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for t in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + t * (end - start), q)
    return end.copy()

q0 = unit([0, 1, 1, 0])
q1 = unit([0, 0, 1, 0])
hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

# Use separate handle locations, 10 cm apart even for the shortest handle.
grasp0 = hammer + np.array([0.0, -0.05, 0.0])
travel_z = max(0.38, hammer[2] + 0.22)

open_gripper_arm1()
park1 = np.array([1.18, 0.0, travel_z + 0.12])
goto_pose_arm1(park1, q1)

open_gripper_arm0()
above = grasp0.copy()
above[2] = travel_z
goto_pose_arm0(above, q0)
p0 = translate(goto_pose_arm0, above, grasp0, q0)
close_gripper_arm0()

p0 = translate(goto_pose_arm0, p0, above, q0)

# Rotate in place while elevated: handle points toward Arm 1 (+X),
# leaving the hammer head on Arm 0's side of the exchange.
for angle in np.linspace(0.0, -np.pi / 2, 19)[1:]:
    c, s = np.cos(angle / 2), np.sin(angle / 2)
    q0 = unit([0.0, (c - s) / np.sqrt(2),
               (c + s) / np.sqrt(2), 0.0])
    goto_pose_arm0(p0, q0)

# Place the handle midpoint at the midpoint between the initial grippers.
handover_center = np.array([(0.44 + 1.18) / 2, 0.0, 0.175])
measured, _ = get_hammer_pose()
measured = np.asarray(measured, dtype=float)
target = p0 + np.array([
    handover_center[0] - measured[0],
    handover_center[1] - measured[1],
    0.0
])
p0 = translate(goto_pose_arm0, p0, target, q0)

measured, _ = get_hammer_pose()
target = p0.copy()
target[2] += handover_center[2] - np.asarray(measured)[2]
p0 = translate(goto_pose_arm0, p0, target, q0)

# The receiver takes the opposite portion of the handle from above.
measured, _ = get_hammer_pose()
grasp1 = np.asarray(measured, dtype=float) + np.array([0.05, 0.0, 0.0])
if np.linalg.norm(grasp1 - p0) < 0.08:
    raise RuntimeError("Insufficient gripper separation for safe handover.")

above1 = grasp1.copy()
above1[2] = travel_z + 0.12
p1 = translate(goto_pose_arm1, park1, above1, q1)
p1 = translate(goto_pose_arm1, p1, grasp1, q1)
close_gripper_arm1()

# Never release the donor before the receiver has closed.
open_gripper_arm0()
retreat0 = p0 + np.array([0.0, 0.0, 0.15])
p0 = translate(goto_pose_arm0, p0, retreat0, q0)
retreat0 = p0 + np.array([-0.15, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat0, q0)