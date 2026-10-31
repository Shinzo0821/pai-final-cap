# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0])
q0_pick /= np.linalg.norm(q0_pick)
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1_transfer = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
clear_z = max(0.35, hammer[2] + 0.20)

# Keep the receiving arm on its own side until the hammer is positioned.
open_gripper_arm1()
receiver = np.array([1.18, 0.0, clear_z])
goto_pose_arm1(receiver, q1_transfer)

# Both grasp points remain on even the shortest handle, 11 cm apart.
open_gripper_arm0()
pickup = hammer + np.array([0.0, -0.055, 0.0])
holder = pickup.copy()
holder[2] = clear_z
goto_pose_arm0(holder, q0_pick)
holder = translate(goto_pose_arm0, holder, pickup, q0_pick)
close_gripper_arm0()

raised = holder.copy()
raised[2] = clear_z
holder = translate(goto_pose_arm0, holder, raised, q0_pick)

# Rotate in place above the table: the handle now points toward Arm 1.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    quaternion = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(holder, quaternion)

# Translate only after rotation, retaining the hammer throughout.
center, _ = get_hammer_pose()
center = np.asarray(center, dtype=float)
target_center = np.array([0.81, 0.0, clear_z])
holder = translate(
    goto_pose_arm0, holder, holder + target_center - center, q0_transfer
)

center, _ = get_hammer_pose()
target_center = np.array([0.81, 0.0, 0.175])
holder = translate(
    goto_pose_arm0,
    holder,
    holder + target_center - np.asarray(center, dtype=float),
    q0_transfer,
)

# Correct residual positioning before bringing the receiving gripper close.
center, _ = get_hammer_pose()
holder = translate(
    goto_pose_arm0,
    holder,
    holder + target_center - np.asarray(center, dtype=float),
    q0_transfer,
)

center, _ = get_hammer_pose()
receive_grasp = np.asarray(center, dtype=float) + np.array([0.055, 0.0, 0.0])
receive_above = receive_grasp.copy()
receive_above[2] = clear_z

receiver = translate(goto_pose_arm1, receiver, receive_above, q1_transfer)
receiver = translate(goto_pose_arm1, receiver, receive_grasp, q1_transfer)
close_gripper_arm1()

# Release only after Arm 1 has closed on the handle.
open_gripper_arm0()
retreat = holder + np.array([-0.14, 0.0, 0.0])
holder = translate(goto_pose_arm0, holder, retreat, q0_transfer)
retreat = holder.copy()
retreat[2] = clear_z
holder = translate(goto_pose_arm0, holder, retreat, q0_transfer)