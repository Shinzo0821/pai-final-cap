# Code block 0
import numpy as np

# Reasoning:
# - The hammer lies along Y. Its handle points to +Y and its head to -Y.
#   get_hammer_pose() returns the middle of the handle.
# - Arm0 grasps the handle 6 cm from its middle, on the head side.
#   Its gripper faces down and opens along X, across the handle.
# - Arm0 then yaws -90 deg about Z to the "opening along Y" orientation [0,1,0,0].
#   Since [0,1,0,0] = Rz(-90) * [0,.707,.707,0], the handle direction turns from +Y to +X.
#   The handle now points toward Arm1 and the head points back toward Arm0.
# - Handover is near the midpoint x = (0.44 + 1.18) / 2 = 0.81, y = 0.
#   Arm0 holds at x = 0.75, so the handle middle is at about 0.81.
#   Arm1 grasps the handle at x = 0.855.
#   That keeps about 10.5 cm between the grippers and stays inside the shortest handle, whose end is about 0.885.
# - Handover height is z = 0.175, inside the required 0.15-0.20 range.
# - Motions are split into steps: lift, then rotate in place, then translate, then lower.

q_arm0_x = np.array([0.0, 0.707, 0.707, 0.0])   # Arm0 down, opening along X
q_arm0_y = np.array([0.0, 1.0, 0.0, 0.0])       # Arm0 down, opening along Y
q_arm1_y = np.array([0.0, 0.0, 1.0, 0.0])       # Arm1 down, opening along Y

hammer_pos, _ = get_hammer_pose()
hammer_pos = np.array(hammer_pos, dtype=float)

grip_offset = 0.06  # distance of Arm0 grasp from handle middle (toward head)
grasp0 = np.array([hammer_pos[0], hammer_pos[1] - grip_offset, hammer_pos[2]])

# Arm0: approach from above and grasp the handle near the head
open_gripper_arm0()
open_gripper_arm1()
goto_pose_arm0(grasp0 + np.array([0.0, 0.0, 0.12]), q_arm0_x)
goto_pose_arm0(grasp0, q_arm0_x, z_approach=0.12)
close_gripper_arm0()

# Lift straight up (translation only)
lift_z = 0.30
goto_pose_arm0(np.array([grasp0[0], grasp0[1], grasp0[2] + 0.08]), q_arm0_x)
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), q_arm0_x)

# Rotate in place (rotation only) so the handle points to +X (toward Arm1)
q_mid = np.array([0.0, 0.924, 0.383, 0.0])  # intermediate yaw (~-45 deg from q_arm0_x)
q_mid = q_mid / np.linalg.norm(q_mid)
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), q_mid)
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), q_arm0_y)

# Translate to the handover location at a safe height, then lower to handover height
mid_x = (0.44 + 1.18) / 2.0
arm0_hold_x = mid_x - grip_offset   # handle middle ends up near mid_x
handover_z = 0.175
hold0_high = np.array([arm0_hold_x, 0.0, lift_z])
goto_pose_arm0(np.array([(grasp0[0] + arm0_hold_x) / 2.0, grasp0[1] / 2.0, lift_z]), q_arm0_y)
goto_pose_arm0(hold0_high, q_arm0_y)
goto_pose_arm0(np.array([arm0_hold_x, 0.0, handover_z]), q_arm0_y)

# Arm1: grasp the handle on the +X side, away from Arm0's gripper
arm1_grasp_x = arm0_hold_x + grip_offset + 0.045
arm1_grasp = np.array([arm1_grasp_x, 0.0, handover_z])
goto_pose_arm1(np.array([1.10, 0.0, handover_z + 0.15]), q_arm1_y)
goto_pose_arm1(arm1_grasp + np.array([0.0, 0.0, 0.15]), q_arm1_y)
goto_pose_arm1(arm1_grasp, q_arm1_y, z_approach=0.15)
close_gripper_arm1()

# Arm0 releases and retreats: up first, then back toward its side
open_gripper_arm0()
goto_pose_arm0(np.array([arm0_hold_x, 0.0, handover_z + 0.12]), q_arm0_y)
goto_pose_arm0(np.array([0.50, 0.0, handover_z + 0.15]), q_arm0_y)

# Arm1 keeps holding the hammer by the handle at handover height
goto_pose_arm1(arm1_grasp, q_arm1_y)