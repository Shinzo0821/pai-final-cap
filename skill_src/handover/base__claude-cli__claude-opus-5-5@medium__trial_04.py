# Code block 0
import numpy as np

# Reasoning:
# - Arm0 grasps the handle near the head end, about 5 cm from the handle middle toward -Y.
# - Arm1 grasps the handle near its free end, about 5 cm from the middle toward +Y.
# - The two grasps are about 10 cm apart, which keeps more than the 8 cm buffer.
# - Arm0 yaws the hammer by -90 deg about Z, so the handle points +X toward Arm1.
#   Arm0 quat [0,0.707,0.707,0] rotated -90 deg about Z gives [0,1,0,0].
# - The handover is near the midpoint (x ~ 0.81, y = 0) at z ~ 0.175.

Q0_X = np.array([0.0, 0.707, 0.707, 0.0])  # arm0 down, opening along X (grips Y-aligned handle)
Q0_Y = np.array([0.0, 1.0, 0.0, 0.0])      # arm0 down, opening along Y (handle along X)
Q1_Y = np.array([0.0, 0.0, 1.0, 0.0])      # arm1 down, opening along Y (grips X-aligned handle)

GRASP_OFF = 0.05      # offset from handle middle for each gripper
HANDOVER_Z = 0.175
SAFE_Z = 0.30
MID_X = 0.81
ARM0_HX = MID_X - GRASP_OFF   # arm0 gripper x at handover
ARM1_HX = MID_X + GRASP_OFF   # arm1 gripper x at handover (handle middle at MID_X)

pos, _ = get_hammer_pose()
pos = np.array(pos, dtype=float)

# ---------- Arm0 grasp ----------
open_gripper_arm0()
open_gripper_arm1()

grasp0 = np.array([pos[0], pos[1] - GRASP_OFF, pos[2]])
# approach from above
goto_pose_arm0(grasp0, Q0_X, z_approach=0.12)
close_gripper_arm0()

# lift straight up (translation only)
lift0 = np.array([grasp0[0], grasp0[1], SAFE_Z])
goto_pose_arm0(np.array([grasp0[0], grasp0[1], grasp0[2] + 0.08]), Q0_X)
goto_pose_arm0(lift0, Q0_X)

# rotate in place at safe height (rotation only), in two steps
c, s = np.cos(np.pi / 8), np.sin(np.pi / 8)
q_half = np.array([0.0, (Q0_X[1] + Q0_Y[1]) / 2, (Q0_X[2] + Q0_Y[2]) / 2, 0.0])
q_half = q_half / np.linalg.norm(q_half)
goto_pose_arm0(lift0, q_half)
goto_pose_arm0(lift0, Q0_Y)

# translate to the handover location at safe height, then descend
goto_pose_arm0(np.array([ARM0_HX, 0.0, SAFE_Z]), Q0_Y)
goto_pose_arm0(np.array([ARM0_HX, 0.0, HANDOVER_Z]), Q0_Y)

# ---------- Arm1 grasp ----------
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)
# handle points +X from arm0; arm1 grasps at middle + offset along X
g1_x = hp[0] + GRASP_OFF
g1_x = max(g1_x, ARM0_HX + 0.09)  # enforce gripper buffer
g1 = np.array([g1_x, hp[1], hp[2]])

# arm1: rotate/position above first (from the right side), then descend
goto_pose_arm1(np.array([g1[0] + 0.10, g1[1], SAFE_Z]), Q1_Y)
goto_pose_arm1(np.array([g1[0], g1[1], SAFE_Z]), Q1_Y)
goto_pose_arm1(g1, Q1_Y)
close_gripper_arm1()

# ---------- Release by Arm0 and retreat ----------
open_gripper_arm0()
cur0 = np.array([ARM0_HX, 0.0, HANDOVER_Z])
goto_pose_arm0(np.array([cur0[0], cur0[1], cur0[2] + 0.10]), Q0_Y)
goto_pose_arm0(np.array([cur0[0] - 0.25, cur0[1], cur0[2] + 0.10]), Q0_Y)

# keep the hammer held by arm1 at handover height
goto_pose_arm1(g1, Q1_Y)