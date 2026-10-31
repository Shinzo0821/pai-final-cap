# Code block 0
import numpy as np

# Reasoning:
# - Hammer lies along Y (handle +Y, head -Y). To grasp a rod along Y, the gripper must open along X.
# - Both arms grasp the handle from above with X-opening. Hands are thin along Y, so we separate
#   the two grasp points along Y: Arm0 grasps the handle on the head side of the handle midpoint,
#   Arm1 grasps toward the +Y (free) end of the handle. Handle half-length >= 0.075m, so both grasp
#   points stay on the handle (not the head).
# - Handover happens at the midpoint between initial gripper positions (x ~ 0.81) with the hammer
#   held at z = 0.175 (within 0.15-0.20). Motions are decomposed: lift -> translate -> lower.
# - Arm1 is parked out of the way (offset in +Y, high z) while Arm0 moves, then descends from above.

Q0_DOWN_OPEN_X = np.array([0.0, 0.707, 0.707, 0.0])   # Arm0 facing down, opening along X
Q1_DOWN_OPEN_X = np.array([0.0, -0.707, 0.707, 0.0])  # Arm1 facing down, opening along X

HANDOVER_X = 0.81
HANDOVER_Z = 0.175
SAFE_Z = 0.32

open_gripper_arm0()
open_gripper_arm1()

# Park Arm1 away from the workspace Arm0 will use
goto_pose_arm1(np.array([1.05, 0.20, SAFE_Z]), Q1_DOWN_OPEN_X)

# Locate hammer handle middle
hammer_pos, _ = get_hammer_pose()
hx, hy, hz = float(hammer_pos[0]), float(hammer_pos[1]), float(hammer_pos[2])

# Arm0 grasp point: slightly toward head side of handle midpoint (still on handle)
grasp0_y = hy - 0.04
goto_pose_arm0(np.array([hx, grasp0_y, hz]), Q0_DOWN_OPEN_X, z_approach=0.12)
close_gripper_arm0()

# Lift straight up
goto_pose_arm0(np.array([hx, grasp0_y, SAFE_Z]), Q0_DOWN_OPEN_X)

# Translate to handover x at safe height
goto_pose_arm0(np.array([HANDOVER_X, grasp0_y, SAFE_Z]), Q0_DOWN_OPEN_X)

# Lower to handover height (hammer z in [0.15, 0.20])
goto_pose_arm0(np.array([HANDOVER_X, grasp0_y, HANDOVER_Z]), Q0_DOWN_OPEN_X)

# Arm1 grasp point: toward the +Y end of the handle, >= 9cm from Arm0's grasp along Y
grasp1_y = hy + 0.05

# Arm1 approaches from above directly over its grasp point
goto_pose_arm1(np.array([HANDOVER_X, grasp1_y, SAFE_Z]), Q1_DOWN_OPEN_X)
goto_pose_arm1(np.array([HANDOVER_X, grasp1_y, HANDOVER_Z]), Q1_DOWN_OPEN_X, z_approach=0.10)
close_gripper_arm1()

# Arm0 releases and retreats upward and back toward its side
open_gripper_arm0()
goto_pose_arm0(np.array([HANDOVER_X, grasp0_y, SAFE_Z]), Q0_DOWN_OPEN_X)
goto_pose_arm0(np.array([0.50, grasp0_y, SAFE_Z]), Q0_DOWN_OPEN_X)