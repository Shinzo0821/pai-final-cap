# Code block 0
import numpy as np

def translate(move, start, end, quat, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quat)
    return end.copy()

q0 = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
safe_z = max(0.40, hammer[2] + 0.20)

open_gripper_arm1()
park1 = np.array([1.18, 0.0, safe_z + 0.10])
goto_pose_arm1(park1, q1)

# Grasp the head-side portion of the handle, leaving its tip available.
open_gripper_arm0()
grasp0 = hammer + np.array([0.0, -0.05, 0.0])
above0 = grasp0.copy()
above0[2] = safe_z
goto_pose_arm0(above0, q0)
pos0 = translate(goto_pose_arm0, above0, grasp0, q0)
close_gripper_arm0()

lifted0 = pos0.copy()
lifted0[2] = safe_z
pos0 = translate(goto_pose_arm0, pos0, lifted0, q0)

# Rotate in place at clearance height. The handle now points toward Arm 1.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    theta = np.pi / 4.0 + angle / 2.0
    q0 = np.array([0.0, np.cos(theta), np.sin(theta), 0.0])
    goto_pose_arm0(pos0, q0)

# Position the handle midpoint at the midpoint between the robots.
hammer_now, _ = get_hammer_pose()
hammer_now = np.asarray(hammer_now, dtype=float)
center_high = np.array([0.81, 0.0, safe_z])
destination0 = pos0 + center_high - hammer_now

lateral0 = destination0.copy()
lateral0[2] = pos0[2]
pos0 = translate(goto_pose_arm0, pos0, lateral0, q0)
pos0 = translate(goto_pose_arm0, pos0, destination0, q0)

hammer_now, _ = get_hammer_pose()
handover_center = np.array([0.81, 0.0, 0.175])
destination0 = pos0 + handover_center - np.asarray(hammer_now)
pos0 = translate(goto_pose_arm0, pos0, destination0, q0)

# The two handle grasps are approximately 10 cm apart.
hammer_now, _ = get_hammer_pose()
hammer_now = np.asarray(hammer_now, dtype=float)
grasp1 = hammer_now + np.array([0.05, 0.0, 0.0])
above1 = grasp1.copy()
above1[2] = park1[2]

pos1 = translate(goto_pose_arm1, park1, above1, q1)
pos1 = translate(goto_pose_arm1, pos1, grasp1, q1)
close_gripper_arm1()

# Release only after Arm 1 has closed on the handle.
open_gripper_arm0()
retreat0 = pos0 + np.array([0.0, 0.0, 0.18])
pos0 = translate(goto_pose_arm0, pos0, retreat0, q0)
translate(goto_pose_arm0, pos0, pos0 + np.array([-0.15, 0.0, 0.0]), q0)