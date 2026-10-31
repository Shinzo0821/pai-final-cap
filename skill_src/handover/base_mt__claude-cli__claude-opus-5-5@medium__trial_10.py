# Code block 0
import numpy as np

# Quaternions (wxyz)
Q0_OPEN_X = np.array([0.0, 0.707, 0.707, 0.0])  # arm0 down, fingers along X: grips a handle lying along Y
Q0_OPEN_Y = np.array([0.0, 1.0, 0.0, 0.0])      # arm0 down, fingers along Y: grips a handle lying along X
Q1_OPEN_Y = np.array([0.0, 0.0, 1.0, 0.0])      # arm1 down, fingers along Y: grips a handle lying along X

# Strategy:
# - Arm0 grasps the handle close to the head (6 cm from the handle middle, toward -Y).
# - Going from Q0_OPEN_X to Q0_OPEN_Y is a -90 deg yaw. That turns the handle from +Y to +X,
#   so the free end of the handle points toward Arm1.
# - At the handover point, Arm1 grasps the free part of the handle from above.
#   It stays more than 8 cm away from the Arm0 gripper and never touches the head.
# - The handover happens near the midpoint x ~ 0.81, y = 0, which is above the gap.
#   Both grippers hold the hammer before Arm0 lets go.

HANDOVER_Z = 0.175
MID_X = 0.81
GRASP_OFFSET_FROM_MID = 0.06  # Arm0 grasp distance from handle middle, toward the head

pos, _ = get_hammer_pose()
pos = np.array(pos, dtype=float)

# ---------- Arm0 grasp ----------
open_gripper_arm0()
grasp0 = np.array([pos[0], pos[1] - GRASP_OFFSET_FROM_MID, pos[2]])
goto_pose_arm0(grasp0, Q0_OPEN_X, z_approach=0.12)
close_gripper_arm0()

# ---------- Lift straight up (translation only) ----------
lift0 = np.array([grasp0[0], grasp0[1], HANDOVER_Z + 0.05])
goto_pose_arm0(lift0, Q0_OPEN_X)

# ---------- Rotate in place: handle swings from +Y to +X ----------
# Use small yaw steps.
for th in [75, 60, 45, 30, 15, 0]:
    a = np.deg2rad(th) / 2.0
    q = np.array([0.0, np.cos(a), np.sin(a), 0.0])
    goto_pose_arm0(lift0, q)
goto_pose_arm0(lift0, Q0_OPEN_Y)

# ---------- Translate to the handover location ----------
# The handle middle sits about GRASP_OFFSET_FROM_MID along +X from the Arm0 gripper.
arm0_hand_x = MID_X - GRASP_OFFSET_FROM_MID
goto_pose_arm0(np.array([arm0_hand_x, lift0[1], HANDOVER_Z + 0.05]), Q0_OPEN_Y)
goto_pose_arm0(np.array([arm0_hand_x, 0.0, HANDOVER_Z + 0.05]), Q0_OPEN_Y)
goto_pose_arm0(np.array([arm0_hand_x, 0.0, HANDOVER_Z]), Q0_OPEN_Y)

# Correct the height so the hammer z is inside [0.15, 0.20].
hpos, _ = get_hammer_pose()
hpos = np.array(hpos, dtype=float)
dz = 0.175 - hpos[2]
if abs(dz) > 0.01:
    goto_pose_arm0(np.array([arm0_hand_x, 0.0, HANDOVER_Z + dz]), Q0_OPEN_Y)
    hpos, _ = get_hammer_pose()
    hpos = np.array(hpos, dtype=float)

# ---------- Arm1 grasps the handle ----------
# Target 5.5 cm past the handle middle, toward the free end.
# That is about 11.5 cm from the Arm0 gripper and 2 cm or more inside the handle end (min length 0.15).
arm0_actual_x = arm0_hand_x
arm1_x = max(hpos[0] + 0.055, arm0_actual_x + 0.11)
arm1_target = np.array([arm1_x, hpos[1], hpos[2]])

open_gripper_arm1()
# Move above the target first, far from Arm0, then descend.
goto_pose_arm1(np.array([arm1_x + 0.10, hpos[1], hpos[2] + 0.15]), Q1_OPEN_Y)
goto_pose_arm1(np.array([arm1_x, hpos[1], hpos[2] + 0.12]), Q1_OPEN_Y)
goto_pose_arm1(arm1_target, Q1_OPEN_Y, z_approach=0.08)
close_gripper_arm1()

# ---------- Arm0 releases and retreats ----------
open_gripper_arm0()
cur_z = HANDOVER_Z + (dz if abs(dz) > 0.01 else 0.0)
goto_pose_arm0(np.array([arm0_hand_x, 0.0, cur_z + 0.10]), Q0_OPEN_Y)
goto_pose_arm0(np.array([0.50, 0.0, cur_z + 0.10]), Q0_OPEN_Y)

# Arm1 keeps holding the hammer by the handle at the handover height.
goto_pose_arm1(arm1_target, Q1_OPEN_Y)