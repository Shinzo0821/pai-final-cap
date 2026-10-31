# Code block 0
import numpy as np

# Arm 0 grasps the handle near the head end (handle_mid - 0.04 along Y).
# Arm 1 grasps the handle toward its free end (handle_mid + 0.05 along X after rotation).
# Separation is about 9 cm, inside the shortest handle (half-length >= 7.5 cm).

q0_x_open = np.array([0.0, 0.70710678, 0.70710678, 0.0])  # arm0 down, opening along X
q0_y_open = np.array([0.0, 1.0, 0.0, 0.0])                # arm0 down, opening along Y
q1_y_open = np.array([0.0, 0.0, 1.0, 0.0])                # arm1 down, opening along Y

# Rotating arm0 from q0_x_open to q0_y_open is a -90 deg yaw.
# This maps the handle direction +Y to +X, so the handle points toward Arm 1.

hammer_pos, _ = get_hammer_pose()
hammer_pos = np.array(hammer_pos, dtype=float)

# ---- Move Arm 1 to a safe waiting pose on its own side ----
open_gripper_arm1()
arm1_wait = np.array([1.10, 0.0, 0.35])
goto_pose_arm1(arm1_wait, q1_y_open)

# ---- Arm 0 grasps the handle near the head ----
open_gripper_arm0()
grasp0 = hammer_pos + np.array([0.0, -0.04, 0.0])
goto_pose_arm0(grasp0, q0_x_open, z_approach=0.12)
close_gripper_arm0()

# Remember the vertical offset between the gripper and the hammer handle
dz = grasp0[2] - hammer_pos[2]

# ---- Lift straight up ----
lift_z = 0.32
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), q0_x_open)

# ---- Rotate in place so the handle points toward +X (Arm 1) ----
q_mid = np.array([0.0, 0.92387953, 0.38268343, 0.0])  # intermediate yaw, -45 deg
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), q_mid)
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), q0_y_open)

# ---- Translate toward the handover point at a safe height (y first, then x) ----
handover_hammer_z = 0.175
arm0_hand_x = 0.76
goto_pose_arm0(np.array([grasp0[0], 0.0, lift_z]), q0_y_open)
goto_pose_arm0(np.array([arm0_hand_x, 0.0, lift_z]), q0_y_open)

# ---- Lower to the handover height (hammer z in [0.15, 0.20]) ----
goto_pose_arm0(np.array([arm0_hand_x, 0.0, handover_hammer_z + dz]), q0_y_open)

# ---- Arm 1 grasps the handle end ----
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)
grasp1 = np.array([hp[0] + 0.05, hp[1], hp[2]])
# Keep at least 8 cm between the grippers
if grasp1[0] - arm0_hand_x < 0.085:
    grasp1[0] = arm0_hand_x + 0.085

# Approach from above on Arm 1's side, then descend
goto_pose_arm1(np.array([grasp1[0] + 0.08, grasp1[1], grasp1[2] + 0.15]), q1_y_open)
goto_pose_arm1(grasp1, q1_y_open, z_approach=0.12)
close_gripper_arm1()

# ---- Arm 0 releases and retreats ----
open_gripper_arm0()
goto_pose_arm0(np.array([arm0_hand_x, 0.0, handover_hammer_z + dz + 0.10]), q0_y_open)
goto_pose_arm0(np.array([0.50, 0.0, handover_hammer_z + dz + 0.15]), q0_y_open)

# ---- Arm 1 holds the hammer at the handover height ----
goto_pose_arm1(grasp1, q1_y_open)