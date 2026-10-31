# Code block 0
import numpy as np

# Open both grippers before starting any movement
open_gripper_arm0()
open_gripper_arm1()

# Define reference quaternions (WXYZ)
# Arm0 facing down opening along X-axis (grasps along Y-axis)
quat_arm0_grasp = np.array([0.0, 0.70710678, 0.70710678, 0.0])
# Arm0 facing down opening along Y-axis
quat_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down opening along Y-axis (grasps along X-axis)
quat_arm1_grasp = np.array([0.0, 0.0, 1.0, 0.0])

# 1. Get initial hammer handle pose
hammer_pos, _ = get_hammer_pose()

# Grasp offset:
# Hammer handle length is between 0.15m and 0.25m.
# Center of handle is at hammer_pos. The head is toward -Y and tip toward +Y.
# Arm0 grasps at -0.045m along Y (toward head, safely on handle).
# Arm1 will grasp at +0.045m along X after rotation (toward tip, safely on handle).
# Separation between grippers = 0.09m (9cm > 8cm collision buffer).
grasp_offset_arm0 = 0.045
arm0_grasp_pos = hammer_pos.copy()
arm0_grasp_pos[1] -= grasp_offset_arm0

# Approach and grasp hammer with Arm0 from above
goto_pose_arm0(arm0_grasp_pos, quat_arm0_grasp, z_approach=0.10)
close_gripper_arm0()

# 2. Lift hammer vertically (decompose into translation component)
lift_height = 0.22
arm0_lift_pos = arm0_grasp_pos.copy()
arm0_lift_pos[2] = lift_height
goto_pose_arm0(arm0_lift_pos, quat_arm0_grasp)

# 3. Rotate hammer 90 degrees around Z (decompose into rotation component)
# This rotates the hammer from Y-axis to X-axis, pointing handle toward Arm1 (+X)
goto_pose_arm0(arm0_lift_pos, quat_arm0_handover)

# 4. Move Arm0 to handover position
# Midpoint between arms in X is (0.44 + 1.18) / 2 = 0.81m
# Handover z must be between 0.15 and 0.20, so choose 0.175m
midpoint_x = 0.81
handover_y = 0.0
handover_z = 0.175

# Hammer center at handover is [midpoint_x, handover_y, handover_z]
# Since Arm0 grasps at -0.045m relative to hammer center in X:
arm0_handover_pos = np.array([midpoint_x - grasp_offset_arm0, handover_y, handover_z])

# Translate Arm0 to handover pose
goto_pose_arm0(arm0_handover_pos, quat_arm0_handover)

# 5. Move Arm1 stepwise to avoid collisions
# Step A: Orient Arm1 and move to safe approach height
arm1_pre_pos = np.array([1.10, handover_y, 0.25])
goto_pose_arm1(arm1_pre_pos, quat_arm1_grasp)

# Step B: Move Arm1 horizontally above handover location
# Arm1 grasps at +0.045m in X relative to hammer center
grasp_offset_arm1 = 0.045
arm1_above_pos = np.array([midpoint_x + grasp_offset_arm1, handover_y, 0.25])
goto_pose_arm1(arm1_above_pos, quat_arm1_grasp)

# Step C: Descend vertically to handover pose
arm1_handover_pos = np.array([midpoint_x + grasp_offset_arm1, handover_y, handover_z])
goto_pose_arm1(arm1_handover_pos, quat_arm1_grasp)

# 6. Complete handover
# Grasp hammer handle with Arm1
close_gripper_arm1()

# Release hammer from Arm0
open_gripper_arm0()

# 7. Retract Arm0 to a safe buffer distance
arm0_retreat_pos = np.array([0.60, handover_y, 0.25])
goto_pose_arm0(arm0_retreat_pos, quat_arm0_handover)