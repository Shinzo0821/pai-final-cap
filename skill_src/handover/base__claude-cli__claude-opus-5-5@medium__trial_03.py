# Code block 0
import numpy as np

# Hammer lies along Y with the handle toward +Y and the head toward -Y.
# get_hammer_pose() returns the middle of the handle.
# Plan:
#  Arm0 grasps the handle near the head end, lifts the hammer, and moves toward the midpoint.
#  Arm0 then rotates -90 deg about world Z so the handle points +X, toward Arm1.
#  Arm1 grasps the free handle end from above, with the grippers about 12 cm apart (more than the 8 cm buffer).
#  The handover height keeps the hammer z between 0.15 and 0.20.

def quat_mul(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    ])

# Arm0 facing down, opening along X (perpendicular to a handle lying along Y)
q0_grasp = np.array([0.0, 0.7071068, 0.7071068, 0.0])
# Rotate -90 deg about world Z so the handle (+Y) ends up pointing +X
qz = np.array([np.cos(-np.pi/4), 0.0, 0.0, np.sin(-np.pi/4)])
q0_handover = quat_mul(qz, q0_grasp)
q0_handover = q0_handover / np.linalg.norm(q0_handover)  # ~[0,1,0,0]

# Arm1 facing down, opening along Y (perpendicular to a handle lying along X)
q1_grasp = np.array([0.0, 0.0, 1.0, 0.0])

ARM0_OFFSET = 0.06   # grasp offset from handle middle toward the head (-Y)
ARM1_OFFSET = 0.06   # grasp offset from handle middle toward the handle end
HANDOVER_Z = 0.175   # target z of the hammer during handover
SAFE_Z = 0.30

open_gripper_arm0()
open_gripper_arm1()

# ---- Arm0 grasps the handle near the head ----
p, _ = get_hammer_pose()
p = np.array(p, dtype=float)
grasp0 = np.array([p[0], p[1] - ARM0_OFFSET, p[2]])

# Approach from above: go above, then descend
goto_pose_arm0(grasp0 + np.array([0, 0, 0.12]), q0_grasp)
goto_pose_arm0(grasp0, q0_grasp, z_approach=0.10)
close_gripper_arm0()

# ---- Lift straight up (translation only) ----
lift0 = np.array([grasp0[0], grasp0[1], max(SAFE_Z, grasp0[2] + 0.15)])
goto_pose_arm0(lift0, q0_grasp)

# ---- Translate toward the handover region (keep orientation, stay high) ----
mid_x = (0.44 + 1.18) / 2.0  # ~0.81
# After rotation, the handle middle sits ARM0_OFFSET in +X from the arm0 gripper.
handover0_xy = np.array([mid_x - ARM0_OFFSET, 0.0])
pre_rot = np.array([handover0_xy[0] - 0.05, handover0_xy[1], lift0[2]])
goto_pose_arm0(pre_rot, q0_grasp)

# ---- Rotate in place (rotation only), in two steps ----
qz_half = np.array([np.cos(-np.pi/8), 0.0, 0.0, np.sin(-np.pi/8)])
q0_mid = quat_mul(qz_half, q0_grasp)
q0_mid = q0_mid / np.linalg.norm(q0_mid)
goto_pose_arm0(pre_rot, q0_mid)
goto_pose_arm0(pre_rot, q0_handover)

# ---- Translate to the handover x, then descend to the handover height ----
goto_pose_arm0(np.array([handover0_xy[0], handover0_xy[1], lift0[2]]), q0_handover)
handover0 = np.array([handover0_xy[0], handover0_xy[1], HANDOVER_Z])
goto_pose_arm0(handover0, q0_handover)

# Correct the height using the measured hammer pose so the hammer z is ~0.175
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)
dz = HANDOVER_Z - hp[2]
if abs(dz) > 0.01:
    handover0 = handover0 + np.array([0, 0, dz])
    goto_pose_arm0(handover0, q0_handover)
    hp, _ = get_hammer_pose()
    hp = np.array(hp, dtype=float)

# ---- Arm1 grasps the free handle end (toward +X) ----
x1 = max(hp[0] + ARM1_OFFSET, handover0[0] + 0.11)  # keep a buffer >= 8 cm from arm0
grasp1 = np.array([x1, hp[1], hp[2]])

# Move arm1 above the target first, staying well away from arm0, then descend
goto_pose_arm1(np.array([grasp1[0] + 0.10, grasp1[1], grasp1[2] + 0.15]), q1_grasp)
goto_pose_arm1(np.array([grasp1[0], grasp1[1], grasp1[2] + 0.12]), q1_grasp)
goto_pose_arm1(grasp1, q1_grasp, z_approach=0.10)
close_gripper_arm1()

# ---- Arm0 releases and retreats ----
open_gripper_arm0()
goto_pose_arm0(handover0 + np.array([0, 0, 0.10]), q0_handover)
goto_pose_arm0(np.array([0.44, 0.0, handover0[2] + 0.10]), q0_handover)