# Code block 0
import numpy as np

# ---------- Perception ----------
hammer_pos, _ = get_hammer_pose()
hx, hy, hz = hammer_pos

# Hammer lies along Y: handle toward +Y, head toward -Y (hammer_pos = middle of handle).
# Arm0 grasps the handle slightly toward the head (-Y) so that a long free stretch of handle
# remains on the +Y side for Arm1 to grasp later.
grasp0 = np.array([hx, hy - 0.04, hz])
q0_down_openX = np.array([0.0, 0.707, 0.707, 0.0])   # fingers close across the Y-aligned handle

# ---------- Arm0: pick up hammer ----------
open_gripper_arm0()
goto_pose_arm0(grasp0, q0_down_openX, z_approach=0.12)
close_gripper_arm0()

# Lift straight up (stay on Arm0's side of the table, above the table surface)
lift_z = 0.175                      # handover height must be in [0.15, 0.20]
lift0 = np.array([hx, hy - 0.04, lift_z])
goto_pose_arm0(lift0, q0_down_openX)

# Move to a rotation spot well on Arm0's side so the hammer stays over the table while rotating
rot_spot = np.array([0.55, 0.0, lift_z])
goto_pose_arm0(rot_spot, q0_down_openX)

# Rotate hammer about Z in two 45-degree steps so the handle end swings toward +X (toward Arm1).
# [0,0.707,0.707,0] -> -45deg -> [0,0.924,0.383,0] -> -45deg -> [0,1,0,0]
q0_mid = np.array([0.0, 0.924, 0.383, 0.0])
q0_down_openY = np.array([0.0, 1.0, 0.0, 0.0])
goto_pose_arm0(rot_spot, q0_mid)
goto_pose_arm0(rot_spot, q0_down_openY)

# Now the handle is aligned along X: head toward -X (Arm0 side), free handle toward +X (Arm1 side).
# Translate to the handover location near the midpoint (~0.81) of the two gripper start positions.
# Arm0 hand at x=0.73, Arm1 will grasp at x=0.83 (10 cm separation along X, hand bodies are thin
# in this direction, keeping clearance between the grippers).
handover0 = np.array([0.73, 0.0, lift_z])
goto_pose_arm0(handover0, q0_down_openY)

# ---------- Arm1: grasp the handle ----------
# Arm1 gripper facing down, opening along Y, so fingers close across the X-aligned handle.
q1_down_openY = np.array([0.0, 0.0, 1.0, 0.0])
handover1 = np.array([0.83, 0.0, lift_z])

open_gripper_arm1()
# Pre-position high above the grasp point, then descend vertically onto the handle
goto_pose_arm1(np.array([0.83, 0.0, lift_z + 0.15]), q1_down_openY)
goto_pose_arm1(handover1, q1_down_openY, z_approach=0.10)
close_gripper_arm1()

# ---------- Arm0: release and retreat ----------
open_gripper_arm0()
# Retreat straight up first, then back toward Arm0's side to avoid any contact with Arm1 / hammer
goto_pose_arm0(np.array([0.73, 0.0, lift_z + 0.15]), q0_down_openY)
goto_pose_arm0(np.array([0.50, 0.0, lift_z + 0.15]), q0_down_openY)