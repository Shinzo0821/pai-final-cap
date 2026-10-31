# Code block 0
import numpy as np

# --- Setup: open both grippers and get hammer pose ---
open_gripper_arm0()
open_gripper_arm1()

hammer_pos, _ = get_hammer_pose()
hx, hy, hz = float(hammer_pos[0]), float(hammer_pos[1]), float(hammer_pos[2])

# Hammer lies along Y (handle toward +Y, head toward -Y).
# Both arms grasp with gripper facing down and fingers closing along X (across the handle).
q_arm0_x_open = np.array([0.0, 0.707, 0.707, 0.0])
q_arm1_x_open = np.array([0.0, -0.707, 0.707, 0.0])  # arm1 is rotated 180 deg about Z w.r.t. arm0

# Grasp offsets along the handle (Y): arm0 slightly toward the head side of the handle middle,
# arm1 toward the free (+Y) end of the handle -> 10cm center-to-center spacing between the hands.
arm0_dy = -0.04
arm1_dy = 0.06

# Handover location: midpoint between initial gripper x positions (~0.81), hammer z in [0.15, 0.20]
handover_x = 0.81
handover_z = 0.175
transport_z = 0.30

# --- Stage arm1 out of the way (up and toward its own side, pre-aligned in Y) ---
goto_pose_arm1(np.array([1.05, hy + arm1_dy, 0.32]), q_arm1_x_open)

# --- Arm0: grasp the hammer handle from above ---
grasp_pos = np.array([hx, hy + arm0_dy, hz])
goto_pose_arm0(grasp_pos, q_arm0_x_open, z_approach=0.12)
close_gripper_arm0()

# --- Arm0: lift straight up (pure translation) ---
goto_pose_arm0(np.array([hx, hy + arm0_dy, transport_z]), q_arm0_x_open)

# --- Arm0: translate horizontally to the handover point (keep orientation and y fixed) ---
goto_pose_arm0(np.array([handover_x, hy + arm0_dy, transport_z]), q_arm0_x_open)

# --- Arm0: lower to handover height so hammer z is within [0.15, 0.20] ---
goto_pose_arm0(np.array([handover_x, hy + arm0_dy, handover_z]), q_arm0_x_open)

# --- Arm1: approach from above and grasp the free part of the handle ---
goto_pose_arm1(np.array([handover_x, hy + arm1_dy, handover_z]), q_arm1_x_open, z_approach=0.15)
close_gripper_arm1()

# --- Arm0: release and retreat upward, leaving arm1 holding the hammer ---
open_gripper_arm0()
goto_pose_arm0(np.array([handover_x, hy + arm0_dy, transport_z]), q_arm0_x_open)
goto_pose_arm0(np.array([0.55, hy + arm0_dy, transport_z]), q_arm0_x_open)