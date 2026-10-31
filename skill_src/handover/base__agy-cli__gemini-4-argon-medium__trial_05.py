# Code block 0
import numpy as np

# 1. Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, _ = get_hammer_pose()

# Reference quaternions (WXYZ)
# Arm0 facing down, gripper fingers opening along X-axis (good for grasping handle aligned along Y-axis)
q_arm0_open_x = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down, gripper fingers opening along Y-axis (rotates hammer handle to align along X-axis)
q_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, gripper fingers opening along Y-axis (good for grasping handle aligned along X-axis)
q_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Ensure both grippers are open initially
open_gripper_arm0()
open_gripper_arm1()

# Move Arm1 to a safe standby position away from the handover zone to avoid any collision
arm1_safe_pos = np.array([1.05, 0.0, 0.25])
goto_pose_arm1(arm1_safe_pos, q_arm1_open_y)

# 2. Pick up the hammer with Arm0
# The hammer lies along the Y-axis with the handle toward +Y and head toward -Y.
# Grasping at a slight negative Y offset (-0.04m from handle center, closer to the head)
# leaves plenty of exposed handle toward the +Y end even for the shortest 0.15m handle.
grasp_y_offset = -0.04
grasp_pos = np.array([hammer_pos[0], hammer_pos[1] + grasp_y_offset, hammer_pos[2]])

# Approach from above and grasp
goto_pose_arm0(grasp_pos, q_arm0_open_x, z_approach=0.12)
close_gripper_arm0()

# 3. Lift the hammer up to handover height (must be between 0.15 and 0.20, so use 0.175)
handover_z = 0.175
lift_pos = np.array([grasp_pos[0], grasp_pos[1], handover_z])
goto_pose_arm0(lift_pos, q_arm0_open_x)

# 4. Rotate Arm0 in place so the hammer handle aligns with the X-axis, pointing toward Arm1 (+X).
# Transitioning from q_arm0_open_x [0, 0.707, 0.707, 0] to q_arm0_open_y [0, 1, 0, 0]
# corresponds to a -90 deg rotation around the world Z-axis, which swings the +Y end of the
# handle (the free end) toward +X (toward Arm1) and the -Y end (the hammer head) toward -X.
goto_pose_arm0(lift_pos, q_arm0_open_y)

# 5. Translate Arm0 to the handover position near the midpoint (midpoint X is ~0.81).
# Because Arm0 holds the handle at 0.04m toward the head (-X), when Arm0 is at x = 0.75,
# the handle center is at x = 0.79, and the free end of the handle extends past x = 0.85.
# Arm1 will grasp at x = 0.84, maintaining a 9cm (0.09m >= 8cm buffer) separation between grippers.
arm0_handover_pos = np.array([0.75, 0.0, handover_z])
goto_pose_arm0(arm0_handover_pos, q_arm0_open_y)

# Check actual hammer pose to ensure exact Z height and Y alignment for Arm1
current_hammer_pos, _ = get_hammer_pose()
arm1_grasp_x = 0.84  # 0.09m away from Arm0 at 0.75, grasping the exposed handle on the +X side
arm1_grasp_y = current_hammer_pos[1]
arm1_grasp_z = np.clip(current_hammer_pos[2], 0.16, 0.19)

arm1_handover_pos = np.array([arm1_grasp_x, arm1_grasp_y, arm1_grasp_z])

# 6. Move Arm1 above the handover grasp point, descend to grasp the handle, and close gripper
goto_pose_arm1(arm1_handover_pos, q_arm1_open_y, z_approach=0.10)
close_gripper_arm1()

# 7. Release Arm0 and retract it safely away to complete the handover
open_gripper_arm0()

# Retract Arm0 upward first, then back toward its home side (-X) to avoid hitting the hammer head
arm0_retract_up = np.array([0.75, 0.0, 0.28])
goto_pose_arm0(arm0_retract_up, q_arm0_open_y)

arm0_home = np.array([0.45, 0.0, 0.28])
goto_pose_arm0(arm0_home, q_arm0_open_y)