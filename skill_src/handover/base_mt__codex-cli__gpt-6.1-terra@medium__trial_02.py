# Code block 0
import numpy as np

q0_pick = np.array([0.0, 0.70710678, 0.70710678, 0.0])
q0_handover = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

open_gripper_arm0()
open_gripper_arm1()

handle_pos, _ = get_hammer_pose()
grasp0 = np.array(handle_pos, dtype=float)
grasp0[1] -= 0.055

# Grasp the head-side portion of the handle, leaving the far end free.
goto_pose_arm0(grasp0, q0_pick, z_approach=0.12)
close_gripper_arm0()

# Lift before rotating, and rotate before translating toward the handover.
lifted = grasp0 + np.array([0.0, 0.0, 0.18])
goto_pose_arm0(lifted, q0_pick)
goto_pose_arm0(lifted, q0_handover)

# The rotation points the free end of the handle toward Arm 1.
hammer_pos, _ = get_hammer_pose()
handover_high = lifted + np.array([0.81 - hammer_pos[0], -hammer_pos[1], 0.0])
goto_pose_arm0(handover_high, q0_handover)

hammer_pos, _ = get_hammer_pose()
handover_low = handover_high + np.array([0.0, 0.0, 0.175 - hammer_pos[2]])
goto_pose_arm0(handover_low, q0_handover)

hammer_pos, _ = get_hammer_pose()
grasp1 = np.array(hammer_pos, dtype=float) + np.array([0.05, 0.0, 0.0])
goto_pose_arm1(grasp1, q1, z_approach=0.12)
close_gripper_arm1()

# Release only after Arm 1 has closed around the handle.
open_gripper_arm0()
goto_pose_arm0(handover_low + np.array([0.0, 0.0, 0.12]), q0_handover)