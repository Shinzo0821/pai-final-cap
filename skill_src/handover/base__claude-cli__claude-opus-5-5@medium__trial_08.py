# Code block 0
import numpy as np

# Quaternions (wxyz)
q0_open_x = np.array([0.0, 0.70710678, 0.70710678, 0.0])   # arm0 down, fingers open along X (grasps a handle lying along Y)
q0_mid = np.array([0.0, 0.92387953, 0.38268343, 0.0])      # arm0 down, halfway through a -90 deg yaw
q0_open_y = np.array([0.0, 1.0, 0.0, 0.0])                 # arm0 down, fingers open along Y (handle now points toward +X)
q1_open_y = np.array([0.0, 0.0, 1.0, 0.0])                 # arm1 down, fingers open along Y (grasps a handle lying along X)

# Strategy:
# Arm0 grasps the handle slightly toward the head and lifts the hammer.
# It then yaws the hammer -90 deg so the handle points +X, toward Arm1.
# The hammer is carried to the midpoint between the arms at a safe height.
# Arm1 comes down from above and grasps the handle end.
# The two grippers stay about 9.5 cm apart along X.

HANDOVER_X_ARM0 = 0.77
HANDOVER_Y = 0.0
SAFE_Z = 0.27
TARGET_HAMMER_Z = 0.175
ARM0_OFFSET = 0.03      # arm0 grasps 3 cm from the handle middle, toward the head
ARM1_OFFSET = 0.065     # arm1 grasps 6.5 cm from the handle middle, toward the handle end

open_gripper_arm0()
open_gripper_arm1()

# Grasp the hammer with arm0
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)
grasp0 = np.array([hp[0], hp[1] - ARM0_OFFSET, hp[2]])
goto_pose_arm0(grasp0 + np.array([0, 0, 0.12]), q0_open_x)
goto_pose_arm0(grasp0, q0_open_x)
close_gripper_arm0()

# Lift the hammer straight up
lift0 = np.array([grasp0[0], grasp0[1], SAFE_Z])
goto_pose_arm0(lift0, q0_open_x)

# Rotate in place, in two steps, so the handle points toward +X
goto_pose_arm0(lift0, q0_mid)
goto_pose_arm0(lift0, q0_open_y)

# Translate toward the handover point at safe height, in two steps
via = np.array([(lift0[0] + HANDOVER_X_ARM0) / 2.0, (lift0[1] + HANDOVER_Y) / 2.0, SAFE_Z])
goto_pose_arm0(via, q0_open_y)
hand0 = np.array([HANDOVER_X_ARM0, HANDOVER_Y, SAFE_Z])
goto_pose_arm0(hand0, q0_open_y)

# Lower to the handover height, then correct using the measured hammer height
hand0 = np.array([HANDOVER_X_ARM0, HANDOVER_Y, TARGET_HAMMER_Z])
goto_pose_arm0(hand0, q0_open_y)
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)
dz = TARGET_HAMMER_Z - hp[2]
if abs(dz) > 0.005:
    hand0 = hand0 + np.array([0, 0, dz])
    goto_pose_arm0(hand0, q0_open_y)
    hp, _ = get_hammer_pose()
    hp = np.array(hp, dtype=float)

# Arm1 grasps the handle toward its free end
grasp1_x = max(hp[0] + ARM1_OFFSET, hand0[0] + 0.09)
grasp1 = np.array([grasp1_x, hp[1], hp[2]])
goto_pose_arm1(np.array([grasp1[0] + 0.05, grasp1[1], SAFE_Z + 0.05]), q1_open_y)
goto_pose_arm1(np.array([grasp1[0], grasp1[1], SAFE_Z + 0.05]), q1_open_y)
goto_pose_arm1(grasp1, q1_open_y, z_approach=0.08)
close_gripper_arm1()

# Release with arm0 and retreat up, then back toward -X
open_gripper_arm0()
goto_pose_arm0(hand0 + np.array([0, 0, 0.10]), q0_open_y)
goto_pose_arm0(hand0 + np.array([-0.15, 0, 0.10]), q0_open_y)

# Arm1 keeps holding the hammer handle at the handover height
goto_pose_arm1(grasp1, q1_open_y)