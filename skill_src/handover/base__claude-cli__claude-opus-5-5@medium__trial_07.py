# Code block 0
import numpy as np

# Plan: Arm0 grasps the handle near the head end, lifts, and yaws 90 deg so the handle points
# toward +X (toward Arm1). It then moves to the handover point near the midpoint (x~0.81).
# Arm1 descends from above and grasps the free handle end, at least 8cm from Arm0's gripper.
# Arm0 releases and retreats toward -X. The hammer stays above the table/handover zone while
# held and is only released once Arm1 has closed on it.

Q0_X = np.array([0.0, 0.70710678, 0.70710678, 0.0])   # arm0 down, opening along X
Q0_MID = np.array([0.0, 0.92387953, 0.38268343, 0.0])  # intermediate yaw
Q0_Y = np.array([0.0, 1.0, 0.0, 0.0])                 # arm0 down, opening along Y; handle ends up along +X
Q1_Y = np.array([0.0, 0.0, 1.0, 0.0])                 # arm1 down, opening along Y

MID_X = 0.81
TARGET_Z = 0.175
ARM0_OFF = 0.055   # arm0 grasp offset from handle middle toward the head
ARM1_OFF = 0.045   # arm1 grasp offset from handle middle toward the handle end

open_gripper_arm0()
open_gripper_arm1()

# Initial hammer pose: lying along Y, handle toward +Y
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)

# Arm0 grasp on the handle near the head (-Y side of the handle middle)
g0 = np.array([hp[0], hp[1] - ARM0_OFF, hp[2]])
goto_pose_arm0(g0, Q0_X, z_approach=0.12)
close_gripper_arm0()

# Lift straight up
cur = g0.copy()
cur[2] = hp[2] + 0.15
goto_pose_arm0(cur.copy(), Q0_X)

# Rotate stepwise in place so the handle points toward +X (toward arm1)
goto_pose_arm0(cur.copy(), Q0_MID)
goto_pose_arm0(cur.copy(), Q0_Y)

# Measure where the handle middle is now relative to the gripper
hp2, _ = get_hammer_pose()
hp2 = np.array(hp2, dtype=float)
off = hp2 - cur  # handle middle relative to gripper

# Translate stepwise toward the handover location: first Y, then X
tgt_g = np.array([MID_X - off[0], 0.0 - off[1], cur[2]])
cur = np.array([cur[0], tgt_g[1], cur[2]])
goto_pose_arm0(cur.copy(), Q0_Y)
cur = np.array([(cur[0] + tgt_g[0]) / 2.0, cur[1], cur[2]])
goto_pose_arm0(cur.copy(), Q0_Y)
cur = tgt_g.copy()
goto_pose_arm0(cur.copy(), Q0_Y)

# Adjust the height so the hammer z is within [0.15, 0.20]
hp3, _ = get_hammer_pose()
hp3 = np.array(hp3, dtype=float)
cur[2] = cur[2] + (TARGET_Z - hp3[2])
goto_pose_arm0(cur.copy(), Q0_Y)

# Final hammer pose for the handover
hp4, _ = get_hammer_pose()
hp4 = np.array(hp4, dtype=float)
if abs(hp4[2] - TARGET_Z) > 0.015:
    cur[2] = cur[2] + (TARGET_Z - hp4[2])
    goto_pose_arm0(cur.copy(), Q0_Y)
    hp4, _ = get_hammer_pose()
    hp4 = np.array(hp4, dtype=float)

# Arm1 grasp point: on the handle toward its free end (+X), at least 8cm from arm0's gripper
g1_x = max(hp4[0] + ARM1_OFF, cur[0] + 0.09)
g1 = np.array([g1_x, hp4[1], hp4[2]])

# Arm1: move above the grasp point from its own side, then descend
above1 = np.array([g1[0] + 0.08, g1[1], g1[2] + 0.15])
goto_pose_arm1(above1, Q1_Y)
goto_pose_arm1(np.array([g1[0], g1[1], g1[2] + 0.12]), Q1_Y)
goto_pose_arm1(g1, Q1_Y)
close_gripper_arm1()

# Arm0 releases and retreats: first up, then back toward its own side
open_gripper_arm0()
cur_up = cur.copy()
cur_up[2] += 0.08
goto_pose_arm0(cur_up, Q0_Y)
retreat = np.array([cur[0] - 0.2, cur[1], cur_up[2]])
goto_pose_arm0(retreat, Q0_Y)