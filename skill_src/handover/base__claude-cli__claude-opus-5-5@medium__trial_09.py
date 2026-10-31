# Code block 0
import numpy as np

# Quaternions (wxyz)
Q0_OPEN_X = np.array([0.0, 0.707, 0.707, 0.0])  # arm0 facing down, fingers open along X (to grasp a handle lying along Y)
Q0_OPEN_Y = np.array([0.0, 1.0, 0.0, 0.0])      # arm0 facing down, fingers open along Y (to hold a handle lying along X)
Q1_OPEN_Y = np.array([0.0, 0.0, 1.0, 0.0])      # arm1 facing down, fingers open along Y

# Handover plan:
# - Arm0 grasps the handle near the head end, so the free part of the handle is left for Arm1.
# - Going from Q0_OPEN_X to Q0_OPEN_Y is a -90 deg yaw about world Z.
#   That rotates the handle direction from +Y to +X, so the handle points toward Arm1.
# - Both grippers approach from above along the same horizontal handle, separated by about 10 cm in X.
# - Handover is near the midpoint of the initial gripper positions (x ~ 0.81, y ~ 0).
#   Handle z is held at ~0.175 m, inside the required [0.15, 0.20] band.

ARM0_GRASP_OFFSET = 0.06   # Arm0 grasps 6 cm from handle middle, toward the head (handle half-length >= 7.5 cm)
SAFE_Z = 0.30
HANDOVER_Z = 0.175
MID_X = 0.81
MID_Y = 0.0

open_gripper_arm0()
open_gripper_arm1()

# ---------- Arm0 picks the hammer ----------
hp, _ = get_hammer_pose()
grasp0 = np.array([hp[0], hp[1] - ARM0_GRASP_OFFSET, hp[2]])

# Approach from above, then descend to grasp
goto_pose_arm0(grasp0, Q0_OPEN_X, z_approach=0.12)
close_gripper_arm0()

# Lift straight up (translation only)
lift0 = np.array([grasp0[0], grasp0[1], SAFE_Z])
goto_pose_arm0(lift0, Q0_OPEN_X)

# Rotate in place at safe height (rotation only): handle now points +X toward Arm1
goto_pose_arm0(lift0, Q0_OPEN_Y)

# ---------- Arm0 moves to the handover pose ----------
# Handle middle ends up ~ARM0_GRASP_OFFSET ahead (+X) of the Arm0 gripper.
# Place the handle middle near the midpoint.
arm0_hand_x = MID_X - ARM0_GRASP_OFFSET
# Translate horizontally at safe height, then descend
goto_pose_arm0(np.array([arm0_hand_x, MID_Y, SAFE_Z]), Q0_OPEN_Y)
goto_pose_arm0(np.array([arm0_hand_x, MID_Y, HANDOVER_Z]), Q0_OPEN_Y)

# ---------- Arm1 grasps the handle ----------
hp2, _ = get_hammer_pose()
# Grasp toward the free end of the handle, at least ~10 cm away from the Arm0 gripper
arm1_x = max(hp2[0] + 0.04, arm0_hand_x + 0.10)
arm1_y = hp2[1]
arm1_z = hp2[2]
# Keep the grasp height within the success band
arm1_z = float(np.clip(arm1_z, 0.155, 0.195))

# Arm1 positions itself high on its own side first, then moves over the grasp point, then descends
goto_pose_arm1(np.array([arm1_x + 0.10, arm1_y, SAFE_Z]), Q1_OPEN_Y)
goto_pose_arm1(np.array([arm1_x, arm1_y, SAFE_Z]), Q1_OPEN_Y)
goto_pose_arm1(np.array([arm1_x, arm1_y, arm1_z]), Q1_OPEN_Y)
close_gripper_arm1()

# ---------- Arm0 releases and retreats ----------
open_gripper_arm0()
# Retreat straight up, then back toward Arm0's side (away from Arm1)
goto_pose_arm0(np.array([arm0_hand_x, MID_Y, SAFE_Z]), Q0_OPEN_Y)
goto_pose_arm0(np.array([0.44, 0.0, SAFE_Z]), Q0_OPEN_Y)

# Arm1 keeps holding the hammer handle at handover height (within 0.15-0.20)
goto_pose_arm1(np.array([arm1_x, arm1_y, arm1_z]), Q1_OPEN_Y)