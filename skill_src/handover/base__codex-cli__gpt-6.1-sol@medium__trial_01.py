# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0])
q1_receive = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

# Both grasp sites remain inside even the shortest handle.
offset = 0.055
clearance_z = max(0.35, float(hammer[2]) + 0.18)
handover_center = np.array([0.81, 0.0, 0.175])

open_gripper_arm1()
park1 = np.array([1.18, 0.0, clearance_z + 0.08])
goto_pose_arm1(park1, q1_receive)

open_gripper_arm0()
grasp0 = hammer + np.array([0.0, -offset, 0.0])
above0 = grasp0.copy()
above0[2] = clearance_z
goto_pose_arm0(above0, q0_pick)
position0 = translate(goto_pose_arm0, above0, grasp0, q0_pick)
close_gripper_arm0()

# Lift vertically before rotating or crossing the table edge.
lift0 = position0.copy()
lift0[2] = clearance_z
position0 = translate(goto_pose_arm0, position0, lift0, q0_pick)

# Rotate about world Z in place: handle +Y becomes +X.
# Arm 0 then holds the left site; Arm 1 receives the right site.
q0_transfer = q0_pick.copy()
for angle in np.linspace(0.0, -np.pi / 2.0, 13)[1:]:
    half = angle / 2.0
    c, s = np.cos(half), np.sin(half)
    q0_transfer = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(position0, q0_transfer)

# Measure the handle center rather than relying on its quaternion.
actual_center, _ = get_hammer_pose()
actual_center = np.asarray(actual_center, dtype=float)
high_center = handover_center.copy()
high_center[2] = clearance_z

target0 = position0 + high_center - actual_center
position0 = translate(goto_pose_arm0, position0, target0, q0_transfer)

actual_center, _ = get_hammer_pose()
target0 = position0 + handover_center - np.asarray(actual_center, dtype=float)
position0 = translate(goto_pose_arm0, position0, target0, q0_transfer)

actual_center, _ = get_hammer_pose()
actual_center = np.asarray(actual_center, dtype=float)
receive1 = actual_center + np.array([offset, 0.0, 0.0])

# Maintain 11 cm horizontal separation throughout the receiving approach.
above1 = receive1.copy()
above1[2] = park1[2]
position1 = translate(goto_pose_arm1, park1, above1, q1_receive)
position1 = translate(goto_pose_arm1, position1, receive1, q1_receive)

# Never release over the gap until the receiving gripper is closed.
close_gripper_arm1()
open_gripper_arm0()

# Withdraw vertically without dragging the open fingers along the handle.
retreat0 = position0 + np.array([0.0, 0.0, 0.14])
position0 = translate(goto_pose_arm0, position0, retreat0, q0_transfer)
retreat0 = position0 + np.array([-0.15, 0.0, 0.0])
position0 = translate(goto_pose_arm0, position0, retreat0, q0_transfer)