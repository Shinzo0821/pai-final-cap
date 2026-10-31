# Code block 0
import numpy as np

q0_pick = np.array([0.0, 0.70710678, 0.70710678, 0.0])
q0_handover = np.array([0.0, 1.0, 0.0, 0.0])
q1_handover = np.array([0.0, 0.0, 1.0, 0.0])

hammer_pos, _ = get_hammer_pose()
hammer_pos = np.array(hammer_pos, dtype=float)

# Grip the handle slightly toward the head, leaving the +Y end free.
grasp0 = hammer_pos + np.array([0.0, -0.045, 0.0])
open_gripper_arm0()
open_gripper_arm1()
goto_pose_arm0(grasp0, q0_pick, z_approach=0.12)
close_gripper_arm0()

# Lift before rotating; rotate in place so the handle points along X.
lift = grasp0.copy()
lift[2] = max(0.18, hammer_pos[2] + 0.12)
goto_pose_arm0(lift, q0_pick)
goto_pose_arm0(lift, q0_handover)

# Move the hammer center to the midpoint, keeping the gripping point to its left.
handover0 = np.array([0.765, 0.0, 0.175])
goto_pose_arm0(np.array([lift[0], lift[1], 0.175]), q0_handover)
goto_pose_arm0(np.array([handover0[0], lift[1], 0.175]), q0_handover)
goto_pose_arm0(handover0, q0_handover)

# Use the measured handle center to locate the free end.
center, _ = get_hammer_pose()
center = np.array(center, dtype=float)
grasp1 = center + np.array([0.045, 0.0, 0.0])
goto_pose_arm1(grasp1, q1_handover, z_approach=0.12)
close_gripper_arm1()

# Transfer only after Arm 1 has closed, then withdraw Arm 0 vertically.
open_gripper_arm0()
goto_pose_arm0(handover0 + np.array([0.0, 0.0, 0.12]), q0_handover)