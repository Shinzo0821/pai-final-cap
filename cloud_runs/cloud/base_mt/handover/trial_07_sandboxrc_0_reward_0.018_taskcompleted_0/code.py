# Code block 0
import numpy as np

# ---------------- Reasoning ----------------
# Hammer lies along Y: handle toward +Y, head toward -Y. get_hammer_pose gives middle of handle.
# Arm0 grasps the handle slightly toward the head side (fingers along X, perpendicular to handle),
# lifts, carries the hammer (still aligned along Y) to the midpoint between the arms at z = 0.175.
# Arm1 then grasps the free +Y portion of the handle, also with fingers along X, offset ~8.5cm in Y
# from Arm0's grasp so the two grippers never overlap. Hammer stays along Y so both grippers come
# straight down and have no need to cross each other.

Q0_DOWN_X = np.array([0.0, 0.707, 0.707, 0.0])    # arm0 facing down, opening along X
Q1_DOWN_X = np.array([0.0, 0.707, -0.707, 0.0])   # arm1 facing down, opening along X (90deg about z from [0,0,1,0])

GRASP0_Y_OFF = -0.03    # arm0 grasp toward hammer head side of handle middle
GRASP1_Y_OFF = 0.055    # arm1 grasp on the free +Y part of handle (>= 8cm from arm0 grasp)
HANDOVER_X = 0.81       # midpoint between initial gripper positions
HANDOVER_Z = 0.175      # required 0.15 - 0.20
CARRY_Z = 0.30
RETREAT_Z = 0.35

# ---------------- Arm0: pick up hammer ----------------
hammer_pos, _ = get_hammer_pose()
hx, hy, hz = float(hammer_pos[0]), float(hammer_pos[1]), float(hammer_pos[2])

open_gripper_arm0()
grasp0 = np.array([hx, hy + GRASP0_Y_OFF, hz])
goto_pose_arm0(grasp0, Q0_DOWN_X, z_approach=0.12)
close_gripper_arm0()

# lift straight up first (pure translation in Z)
goto_pose_arm0(np.array([hx, hy + GRASP0_Y_OFF, CARRY_Z]), Q0_DOWN_X)

# translate at carry height to the handover point (above the center region)
handover_y0 = hy + GRASP0_Y_OFF
goto_pose_arm0(np.array([HANDOVER_X, handover_y0, CARRY_Z]), Q0_DOWN_X)

# lower to handover height (hammer z in [0.15, 0.20])
goto_pose_arm0(np.array([HANDOVER_X, handover_y0, HANDOVER_Z]), Q0_DOWN_X)

# ---------------- Arm1: grasp handle ----------------
handover_y1 = hy + GRASP1_Y_OFF   # same world Y offset relative to hammer; hammer kept along Y
open_gripper_arm1()

# first rise/stay high above the handover area, aligned over the handle grasp point
goto_pose_arm1(np.array([HANDOVER_X, handover_y1, RETREAT_Z]), Q1_DOWN_X)

# descend vertically onto the handle (fingers along X straddle the Y-aligned handle)
goto_pose_arm1(np.array([HANDOVER_X, handover_y1, HANDOVER_Z]), Q1_DOWN_X, z_approach=0.10)
close_gripper_arm1()

# ---------------- Arm0: release and retreat ----------------
open_gripper_arm0()
goto_pose_arm0(np.array([HANDOVER_X, handover_y0, RETREAT_Z]), Q0_DOWN_X)
goto_pose_arm0(np.array([0.5, handover_y0, RETREAT_Z]), Q0_DOWN_X)