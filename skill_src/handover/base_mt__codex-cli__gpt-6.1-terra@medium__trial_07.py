# Code block 0
import numpy as np

q_pick = np.array([0.0, 0.70710678, 0.70710678, 0.0])
q_transfer0 = np.array([0.0, 1.0, 0.0, 0.0])
q_transfer1 = np.array([0.0, 0.0, 1.0, 0.0])

hammer_pos, _ = get_hammer_pose()
hammer_pos = np.asarray(hammer_pos, dtype=float)

# Grasp the handle on the head side, leaving the far end free for Arm 1.
grasp0 = hammer_pos + np.array([0.0, -0.05, 0.0])
open_gripper_arm0()
open_gripper_arm1()
goto_pose_arm0(grasp0, q_pick, z_approach=0.12)
close_gripper_arm0()

# Lift and rotate above the table before translating toward the handover.
lift0 = grasp0 + np.array([0.0, 0.0, 0.14])
goto_pose_arm0(lift0, q_pick)
goto_pose_arm0(lift0, q_transfer0)

# Measure the held hammer's position after rotation and place its center
# at the handover midpoint and within the required height band.
held_pos, _ = get_hammer_pose()
held_pos = np.asarray(held_pos, dtype=float)
target_hammer = np.array([0.81, 0.0, 0.175])
target0 = lift0 + (target_hammer - held_pos)

for fraction in (0.25, 0.5, 0.75, 1.0):
    goto_pose_arm0(lift0 + fraction * (target0 - lift0), q_transfer0)

# Approach the free handle end vertically, keeping the grippers separated.
held_pos, _ = get_hammer_pose()
held_pos = np.asarray(held_pos, dtype=float)
grasp1 = held_pos + np.array([0.05, 0.0, 0.0])
goto_pose_arm1(grasp1, q_transfer1, z_approach=0.12)
close_gripper_arm1()
open_gripper_arm0()

# Withdraw Arm 0 vertically before moving it away.
goto_pose_arm0(target0 + np.array([0.0, 0.0, 0.12]), q_transfer0)