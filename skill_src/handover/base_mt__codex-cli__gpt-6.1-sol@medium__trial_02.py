# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0])
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1_transfer = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, finish, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    finish = np.asarray(finish, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(finish - start) / step)))
    for i in range(1, count + 1):
        move(start + (finish - start) * i / count, quaternion)
    return finish.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

# Two handle grasps 11 cm apart fit even the shortest handle.
offset = 0.055
pickup = hammer + np.array([0.0, -offset, 0.0])
safe_z = max(0.35, hammer[2] + 0.20)
park1 = np.array([1.18, 0.0, safe_z + 0.12])

open_gripper_arm1()
goto_pose_arm1(park1, q1_transfer)

open_gripper_arm0()
above = pickup.copy()
above[2] = safe_z
goto_pose_arm0(above, q0_pick)
p0 = translate(goto_pose_arm0, above, pickup, q0_pick, step=0.015)
close_gripper_arm0()
lifted = p0.copy()
lifted[2] = safe_z
p0 = translate(goto_pose_arm0, p0, lifted, q0_pick)

# Rotate in place while elevated: handle +Y becomes +X.
# Arm 0 holds the left end; Arm 1 can approach the right end.
for angle in np.linspace(0.0, -np.pi / 2.0, 13)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    q = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(p0, q)

# Use measured handle-center position rather than trusting the object quaternion.
measured, _ = get_hammer_pose()
measured = np.asarray(measured, dtype=float)
high_center = np.array([0.81, 0.0, safe_z])
destination = p0 + high_center - measured

waypoint = p0.copy()
waypoint[1] = destination[1]
p0 = translate(goto_pose_arm0, p0, waypoint, q0_transfer)
waypoint = p0.copy()
waypoint[0] = destination[0]
p0 = translate(goto_pose_arm0, p0, waypoint, q0_transfer)
p0 = translate(goto_pose_arm0, p0, destination, q0_transfer)

# Lower the hammer alone before bringing the receiving gripper close.
measured, _ = get_hammer_pose()
destination = p0 + np.array([0.0, 0.0, 0.175 - measured[2]])
p0 = translate(goto_pose_arm0, p0, destination, q0_transfer, step=0.015)

center, _ = get_hammer_pose()
center = np.asarray(center, dtype=float)
receive = center + np.array([offset, 0.0, 0.0])
above_receive = receive.copy()
above_receive[2] = park1[2]

p1 = translate(goto_pose_arm1, park1, above_receive, q1_transfer)
p1 = translate(goto_pose_arm1, p1, receive, q1_transfer, step=0.01)

# Maintain overlapping support over the gap until Arm 1 has closed.
close_gripper_arm1()
open_gripper_arm0()

retreat = p0 + np.array([0.0, 0.0, 0.15])
p0 = translate(goto_pose_arm0, p0, retreat, q0_transfer, step=0.015)
retreat = p0.copy()
retreat[0] = 0.44
p0 = translate(goto_pose_arm0, p0, retreat, q0_transfer)