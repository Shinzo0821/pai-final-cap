# Code block 0
import numpy as np

# ---------------- Parameters ----------------
# Quaternions (wxyz). Down-facing gripper with yaw psi about world Z: [0, cos(psi/2), sin(psi/2), 0]
Q0_OPEN_X = np.array([0.0, 0.70710678, 0.70710678, 0.0])  # Arm0 down, opening along X (straddles a Y-aligned handle)
Q0_OPEN_Y = np.array([0.0, 1.0, 0.0, 0.0])                # Arm0 down, opening along Y (straddles an X-aligned handle)
Q1_OPEN_Y = np.array([0.0, 0.0, 1.0, 0.0])                # Arm1 down, opening along Y (straddles an X-aligned handle)

# Handover location: midpoint of the initial gripper positions
mid_x = (0.44 + 1.18) / 2.0   # ~0.81
mid_y = 0.0
handover_z = 0.175            # target hammer z during handover (inside 0.15-0.20)

# Handle half-length is at least 0.075 m. Arm0 grasps the handle near the head end
# (0.06 m from the handle middle, toward the head). This leaves most of the handle free for Arm1.
arm0_offset = 0.06
# Arm1 grasps 0.04 m from the handle middle, toward the handle end.
# Gripper separation = 0.10 m, which keeps the 8 cm buffer.
arm1_offset = 0.04

# ---------------- Step 1: Read hammer pose ----------------
hammer_pos, _ = get_hammer_pose()
hammer_pos = np.array(hammer_pos, dtype=float)
hx, hy, hz = hammer_pos

# The handle points to +Y and the head to -Y, so the Arm0 grasp is at -Y from the handle middle.
grasp0 = np.array([hx, hy - arm0_offset, hz])

# ---------------- Step 2: Arm0 grasps the hammer handle ----------------
open_gripper_arm0()
open_gripper_arm1()

# Move above the grasp point with the correct orientation first.
goto_pose_arm0(grasp0 + np.array([0.0, 0.0, 0.15]), Q0_OPEN_X)
# Descend straight down onto the handle.
goto_pose_arm0(grasp0, Q0_OPEN_X, z_approach=0.10)
close_gripper_arm0()

# ---------------- Step 3: Lift straight up ----------------
lift_z = max(hz + 0.20, 0.30)
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), Q0_OPEN_X)

# ---------------- Step 4: Rotate in place (pure rotation) ----------------
# Yaw by -90 deg: the handle direction changes from +Y to +X, so it points toward Arm1.
# The head points toward Arm0 (-X). Arm1 can then grasp the free handle end from above.
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), Q0_OPEN_Y)

# ---------------- Step 5: Translate toward the handover point ----------------
# Arm0 gripper position at handover, so that the handle middle sits slightly +X of the midpoint.
arm0_hand_x = mid_x - 0.05
# First move in the horizontal plane at a safe height.
goto_pose_arm0(np.array([arm0_hand_x, mid_y, lift_z]), Q0_OPEN_Y)
# Then lower to the handover height.
goto_pose_arm0(np.array([arm0_hand_x, mid_y, handover_z]), Q0_OPEN_Y)

# ---------------- Step 6: Arm1 approaches and grasps the handle ----------------
# Handle middle is at arm0_hand_x + arm0_offset along +X.
handle_mid_x = arm0_hand_x + arm0_offset
grasp1 = np.array([handle_mid_x + arm1_offset, mid_y, handover_z])

# Re-measure the hammer to refine the Arm1 grasp height and y (in case the hammer slipped).
cur_pos, _ = get_hammer_pose()
cur_pos = np.array(cur_pos, dtype=float)
if abs(cur_pos[1] - mid_y) < 0.05:
    grasp1[1] = cur_pos[1]
if 0.10 < cur_pos[2] < 0.25:
    grasp1[2] = cur_pos[2]

# Pre-position Arm1 high above, on its own side, with the correct orientation.
goto_pose_arm1(np.array([grasp1[0] + 0.08, grasp1[1], grasp1[2] + 0.20]), Q1_OPEN_Y)
# Move above the grasp point.
goto_pose_arm1(np.array([grasp1[0], grasp1[1], grasp1[2] + 0.15]), Q1_OPEN_Y)
# Descend vertically onto the handle.
goto_pose_arm1(grasp1, Q1_OPEN_Y, z_approach=0.10)
close_gripper_arm1()

# ---------------- Step 7: Arm0 releases and retreats ----------------
open_gripper_arm0()
# Move up first, away from the hammer head.
goto_pose_arm0(np.array([arm0_hand_x, mid_y, handover_z + 0.12]), Q0_OPEN_Y)
# Then move back toward the Arm0 side.
goto_pose_arm0(np.array([0.44, 0.0, handover_z + 0.12]), Q0_OPEN_Y)

# Arm1 keeps holding the hammer handle at the handover height (z within 0.15-0.20).
goto_pose_arm1(grasp1, Q1_OPEN_Y)