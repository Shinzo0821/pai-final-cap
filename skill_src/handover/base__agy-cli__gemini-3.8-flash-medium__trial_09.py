# Code block 0
import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Define reference quaternions
# Arm 0: facing down, opening along X-axis (to grasp hammer lying along Y-axis)
q_arm0_pickup = np.array([0.0, 0.707, 0.707, 0.0])
# Arm 0: facing down, opening along Y-axis (rotates hammer by 90 deg so handle points along +X)
q_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm 1: facing down, opening along Y-axis (grasps handle oriented along X-axis)
q_arm1_handover = np.array([0.0, 0.0, 1.0, 0.0])

# Get hammer pose (middle of handle)
hammer_pos, _ = get_hammer_pose()

# Grasp hammer handle slightly towards the head (-Y direction by 4.5 cm)
# This leaves ample room on the +Y side for Arm 1 to grasp later
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] - 0.045, hammer_pos[2]])

# 1. Arm 0 approaches and grasps hammer from the table
goto_pose_arm0(grasp_pos_arm0, q_arm0_pickup, z_approach=0.10)
close_gripper_arm0()

# Handover constraints:
# - Midpoint between Arm 0 (x ≈ 0.44) and Arm 1 (x ≈ 1.18): x_mid = 0.81, y_mid = 0.0
# - Handover z must be between 0.15 and 0.20: choose z = 0.175
z_handover = 0.175
x_mid = 0.81
y_mid = 0.0

# 2. Lift hammer vertically to handover height
goto_pose_arm0(np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], z_handover]), q_arm0_pickup)

# 3. Rotate Arm 0 in place by 90 degrees around Z to align hammer along X-axis
# Handle now points toward +X (Arm 1 side), head points toward -X (Arm 0 side)
goto_pose_arm0(np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], z_handover]), q_arm0_handover)

# 4. Translate Arm 0 horizontally to handover position
# Center of handle will be at x_mid=0.81; Arm 0 is grasping at -4.5 cm along X
arm0_handover_pos = np.array([x_mid - 0.045, y_mid, z_handover])
goto_pose_arm0(arm0_handover_pos, q_arm0_handover)

# 5. Arm 1 moves stepwise to grasp handle:
# Arm 1 grasps at +4.5 cm along X (9 cm buffer between grippers > 8 cm requirement)
arm1_grasp_pos = np.array([x_mid + 0.045, y_mid, z_handover])

# Pre-position Arm 1: rotate to handover orientation at elevated Z to avoid collision
goto_pose_arm1(np.array([1.18, 0.0, z_handover + 0.10]), q_arm1_handover)

# Translate Arm 1 horizontally above grasp target
goto_pose_arm1(np.array([arm1_grasp_pos[0], arm1_grasp_pos[1], z_handover + 0.10]), q_arm1_handover)

# Lower Arm 1 vertically to grasp position
goto_pose_arm1(arm1_grasp_pos, q_arm1_handover)

# 6. Execute handover
close_gripper_arm1()
open_gripper_arm0()

# 7. Retract Arm 0 safely away from Arm 1
goto_pose_arm0(np.array([arm0_handover_pos[0] - 0.15, arm0_handover_pos[1], z_handover]), q_arm0_handover)