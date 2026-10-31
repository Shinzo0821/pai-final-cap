# Code block 0
import numpy as np

# Plan:
# 1. Arm0 grasps the handle near the head end (handle middle - 0.035 in Y), so there is room
#    on the handle for Arm1 to grasp toward the free end.
# 2. Lift, then yaw the gripper so the handle points +X toward Arm1.
# 3. Move to just left of the midpoint of the two arms (x ~ 0.81) and hold the hammer at z ~ 0.175.
# 4. Arm1 grasps the handle end side from above, about 9.5cm in +X from Arm0's gripper.
# 5. Arm0 releases and retreats up and back toward its own side.

Q0_OPEN_X = np.array([0.0, 0.707, 0.707, 0.0])   # Arm0 down, opening along X (handle along Y)
Q0_OPEN_Y = np.array([0.0, 1.0, 0.0, 0.0])       # Arm0 down, opening along Y (handle along X)
Q1_OPEN_Y = np.array([0.0, 0.0, 1.0, 0.0])       # Arm1 down, opening along Y (handle along X)

HANDOVER_X_MID = 0.81
HANDOVER_Y = 0.0
TARGET_Z = 0.175
SAFE_Z = 0.30

open_gripper_arm0()
open_gripper_arm1()

# Step 1: Arm0 grasps the handle near the head end.
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)
grasp0 = np.array([hp[0], hp[1] - 0.035, hp[2]])
goto_pose_arm0(grasp0, Q0_OPEN_X, z_approach=0.12)
close_gripper_arm0()

# Step 2: Lift straight up.
lift_z = max(grasp0[2] + 0.15, SAFE_Z)
lift0 = np.array([grasp0[0], grasp0[1], lift_z])
goto_pose_arm0(lift0, Q0_OPEN_X)

# Rotate in place (yaw -90 deg) so the handle points toward +X (toward Arm1).
goto_pose_arm0(lift0, Q0_OPEN_Y)

# Step 3: Move toward the handover point at a safe height.
# Arm0 gripper stays about 4.5cm left of the midpoint, so the handle extends toward Arm1.
hand0_x = HANDOVER_X_MID - 0.045
goto_pose_arm0(np.array([lift0[0] + 0.5 * (hand0_x - lift0[0]), HANDOVER_Y, lift_z]), Q0_OPEN_Y)
goto_pose_arm0(np.array([hand0_x, HANDOVER_Y, lift_z]), Q0_OPEN_Y)

# Descend to the handover height.
goto_pose_arm0(np.array([hand0_x, HANDOVER_Y, TARGET_Z]), Q0_OPEN_Y)

# Correct the height using the measured hammer pose so that hammer z is about 0.175.
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)
dz = TARGET_Z - hp[2]
arm0_z = TARGET_Z + dz
if abs(dz) > 0.005:
    goto_pose_arm0(np.array([hand0_x, HANDOVER_Y, arm0_z]), Q0_OPEN_Y)
    hp, _ = get_hammer_pose()
    hp = np.array(hp, dtype=float)

# Step 4: Arm1 grasps the handle toward its free end (+X side).
# The handle middle is about 0.035 in +X of Arm0's gripper; grasp at middle + 0.06,
# which gives about 9.5cm of gripper separation and stays within the minimum handle half-length (0.075).
grasp1_x = max(hp[0] + 0.06, hand0_x + 0.09)
grasp1 = np.array([grasp1_x, hp[1], hp[2]])

# Approach from the right side at a safe height, then descend vertically.
goto_pose_arm1(np.array([grasp1_x + 0.10, hp[1], SAFE_Z]), Q1_OPEN_Y)
goto_pose_arm1(np.array([grasp1_x, hp[1], SAFE_Z]), Q1_OPEN_Y)
goto_pose_arm1(grasp1, Q1_OPEN_Y, z_approach=0.10)
close_gripper_arm1()

# Step 5: Arm0 releases and retreats up and away toward its own side.
open_gripper_arm0()
goto_pose_arm0(np.array([hand0_x, HANDOVER_Y, arm0_z + 0.12]), Q0_OPEN_Y)
goto_pose_arm0(np.array([hand0_x - 0.15, HANDOVER_Y, arm0_z + 0.12]), Q0_OPEN_Y)

# Arm1 holds the hammer by the handle, staying within the valid z range and moving slightly toward its own side.
goto_pose_arm1(np.array([grasp1_x + 0.05, hp[1], grasp1[2]]), Q1_OPEN_Y)