# Code block 0
import numpy as np

# Retrieve the initial pose of the hammer handle center
hammer_pos, _ = get_hammer_pose()

# Reference orientations in robot0 base frame
# Arm 0 facing down, opening along X-axis (for grasping object along Y-axis)
q_arm0_pick = np.array([0.0, 0.707, 0.707, 0.0])
# Arm 0 facing down, opening along Y-axis (rotates grasped object to X-axis)
q_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm 1 facing down, opening along Y-axis (for grasping object along X-axis)
q_arm1_grasp = np.array([0.0, 0.0, 1.0, 0.0])

# Handover specifications:
# - Target handover Z: 0.175m (must be strictly between 0.15m and 0.20m)
# - Target handover X midpoint: (0.44 + 1.18) / 2 = 0.81m
# - Minimum buffer between grippers: >= 8cm (0.08m)
z_handover = 0.175
x_midpoint = 0.81

# Grasp offset relative to handle center:
# The handle length is 0.15m - 0.25m (half-length >= 0.075m).
# Head is toward -Y, handle end is toward +Y.
# Arm 0 grasps at -0.045m toward head (safely on handle, 4.5cm from center).
arm0_pick_pos = hammer_pos + np.array([0.0, -0.045, 0.0])

# Prepare Arm 0 gripper
open_gripper_arm0()

# Step 1: Arm 0 approaches and grasps the hammer handle
goto_pose_arm0(arm0_pick_pos, q_arm0_pick, z_approach=0.1)
close_gripper_arm0()

# Step 2: Safe stepwise motion to handover pose (decoupling translation and rotation)
# 2a. Lift hammer vertically to handover height
goto_pose_arm0(np.array([arm0_pick_pos[0], arm0_pick_pos[1], z_handover]), q_arm0_pick)

# 2b. Rotate in place: aligns hammer handle along +X pointing toward Arm 1
goto_pose_arm0(np.array([arm0_pick_pos[0], arm0_pick_pos[1], z_handover]), q_arm0_handover)

# 2c. Translate along Y to table center (y = 0.0)
goto_pose_arm0(np.array([arm0_pick_pos[0], 0.0, z_handover]), q_arm0_handover)

# Handover poses:
# After 90-degree rotation, the grasp offset [-0.045, 0, 0] points toward -X.
# Arm 0 grasp at x = 0.765m places the handle center at x = 0.81m.
# Arm 1 grasps at x = 0.855m (+0.045m toward handle end).
# Distance between grippers: 0.855 - 0.765 = 0.09m (9cm > 8cm required buffer).
arm0_handover_pos = np.array([x_midpoint - 0.045, 0.0, z_handover])
arm1_handover_pos = np.array([x_midpoint + 0.045, 0.0, z_handover])

# 2d. Move Arm 0 along X to handover position
goto_pose_arm0(arm0_handover_pos, q_arm0_handover)

# Step 3: Arm 1 stepwise approach to grasp the hammer handle
open_gripper_arm1()

# 3a. Orient Arm 1 at initial safe elevated position
goto_pose_arm1(np.array([1.18, 0.0, z_handover + 0.1]), q_arm1_grasp)

# 3b. Translate Arm 1 horizontally along X above the handover position
goto_pose_arm1(np.array([arm1_handover_pos[0], arm1_handover_pos[1], z_handover + 0.1]), q_arm1_grasp)

# 3c. Descend vertically along Z to grasp the handle
goto_pose_arm1(arm1_handover_pos, q_arm1_grasp)

# 3d. Close Arm 1 gripper to secure the handle
close_gripper_arm1()

# Step 4: Transfer completion - Arm 0 releases and retreats safely
open_gripper_arm0()
goto_pose_arm0(np.array([arm0_handover_pos[0] - 0.15, 0.0, z_handover]), q_arm0_handover)