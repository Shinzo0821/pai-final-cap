# Code block 0
import numpy as np

# Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, _ = get_hammer_pose()

# Reference quaternions (WXYZ)
# Arm0 facing down, opening along X-axis (good for grasping handle aligned along Y-axis)
q_arm0_open_x = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down, opening along Y-axis (rotates hammer so handle aligns along X-axis)
q_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, opening along Y-axis (good for grasping handle aligned along X-axis)
q_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Ensure both grippers are open initially
open_gripper_arm0()
open_gripper_arm1()

# Step 1: Arm 0 grasps the hammer near the head (-Y end of the handle)
# The hammer lies along the Y-axis with the handle toward +Y and head toward -Y.
# Handle length is between 0.15m and 0.25m. Grasping at y - 0.04m leaves the +Y end free for Arm 1.
pick_pos = np.array([hammer_pos[0], hammer_pos[1] - 0.04, hammer_pos[2]])
goto_pose_arm0(pick_pos, q_arm0_open_x, z_approach=0.10)
close_gripper_arm0()

# Step 2: Lift the hammer to handover height (must be between 0.15 and 0.20)
handover_z = 0.175
lift_pos = np.array([pick_pos[0], pick_pos[1], handover_z])
goto_pose_arm0(lift_pos, q_arm0_open_x)

# Step 3: Rotate Arm 0 in place so the hammer handle points toward Arm 1 (+X direction)
# Rotating from [0, 0.707, 0.707, 0] to [0, 1, 0, 0] is a -90 deg rotation around Z,
# which swings the +Y end of the handle to point toward +X.
goto_pose_arm0(lift_pos, q_arm0_open_y)

# Step 4: Move Arm 0 to the handover position near the midpoint (x = (0.44 + 1.18)/2 = 0.81)
# Since Arm 0 holds the hammer at 0.04m from the handle center, placing Arm 0 at x = 0.76
# puts the handle center at x = 0.80 and the free end of the handle extending past x = 0.87.
arm0_handover_pos = np.array([0.76, 0.0, handover_z])
goto_pose_arm0(arm0_handover_pos, q_arm0_open_y)

# Step 5: Move Arm 1 to grasp the exposed handle
# Check actual hammer pose to ensure precise alignment while keeping >= 8cm buffer between grippers
curr_hammer_pos, _ = get_hammer_pose()
arm1_grasp_x = max(arm0_handover_pos[0] + 0.09, curr_hammer_pos[0] + 0.05)
arm1_handover_pos = np.array([arm1_grasp_x, curr_hammer_pos[1], curr_hammer_pos[2]])

# Approach from above and grasp the handle with Arm 1
goto_pose_arm1(arm1_handover_pos, q_arm1_open_y, z_approach=0.10)
close_gripper_arm1()

# Step 6: Release Arm 0 and retract it safely to complete the handover
open_gripper_arm0()
arm0_retract_above = np.array([arm0_handover_pos[0], arm0_handover_pos[1], handover_z + 0.10])
goto_pose_arm0(arm0_retract_above, q_arm0_open_y)

arm0_home = np.array([0.44, 0.0, handover_z + 0.10])
goto_pose_arm0(arm0_home, q_arm0_open_y)