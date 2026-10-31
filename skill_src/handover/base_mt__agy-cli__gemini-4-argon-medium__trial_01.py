# Code block 0
import numpy as np

# 1. Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, _ = get_hammer_pose()

# Reference quaternions (WXYZ)
# Arm0 facing down, fingers opening along X-axis (suitable for grasping handle aligned along Y-axis)
q_arm0_open_x = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down, fingers opening along Y-axis (rotates hammer 90 deg around Z so handle aligns with X-axis)
q_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, fingers opening along Y-axis (suitable for grasping handle aligned along X-axis)
q_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Ensure both grippers are open initially
open_gripper_arm0()
open_gripper_arm1()

# 2. Pick up the hammer with Arm 0
# The hammer lies along the Y-axis (+Y handle, -Y head).
# Grasp slightly toward the -Y side (closer to head/middle) so that when rotated toward +X,
# plenty of handle extends toward Arm 1 (+X) while keeping >= 8cm buffer between grippers.
# Since handle length is 0.15m to 0.25m, grasping at y_offset = -0.04m from handle center
# leaves ~0.115m to 0.165m of handle on the +Y side, and stays safely away from the head.
grasp_offset = -0.04
arm0_pick_pos = np.array([hammer_pos[0], hammer_pos[1] + grasp_offset, hammer_pos[2]])

# Approach and grasp with Arm 0
goto_pose_arm0(arm0_pick_pos, q_arm0_open_x, z_approach=0.12)
close_gripper_arm0()

# 3. Lift the hammer to handover height (z between 0.15 and 0.20 -> use 0.18)
handover_z = 0.18
arm0_lifted_pos = np.array([arm0_pick_pos[0], arm0_pick_pos[1], handover_z])
goto_pose_arm0(arm0_lifted_pos, q_arm0_open_x)

# 4. Rotate hammer in place so the handle points toward Arm 1 (+X direction)
# Rotating from q_arm0_open_x ([0, 0.707, 0.707, 0]) to q_arm0_open_y ([0, 1, 0, 0])
# corresponds to a -90 deg rotation around Z, swinging the +Y end of the handle to +X.
goto_pose_arm0(arm0_lifted_pos, q_arm0_open_y)

# 5. Move Arm 0 to the handover position near the midpoint (midpoint X is ~(0.44 + 1.18)/2 = 0.81)
# Read current hammer pose after rotation to verify handle center offset relative to Arm 0
curr_hammer_pos, _ = get_hammer_pose()

# Position Arm 0 slightly to the left of the midpoint so the handle spans across X = 0.81
# If Arm 0 is at X = 0.76, the handle center is at ~0.80, and the free end extends to ~0.87+.
arm0_handover_pos = np.array([0.76, 0.0, handover_z])
goto_pose_arm0(arm0_handover_pos, q_arm0_open_y)

# Re-check hammer handle center at the handover configuration
handover_hammer_pos, _ = get_hammer_pose()

# 6. Move Arm 1 to grasp the hammer handle
# Maintain at least an 8cm (0.08m) buffer between Arm 0 (at X = 0.76) and Arm 1.
# Placing Arm 1 at X = 0.85 gives a 9cm buffer from Arm 0's gripper while grasping
# the handle ~5cm from its center (well within the 7.5cm to 12.5cm half-length).
arm1_grasp_x = max(arm0_handover_pos[0] + 0.09, handover_hammer_pos[0] + 0.04)
arm1_handover_pos = np.array([arm1_grasp_x, handover_hammer_pos[1], handover_hammer_pos[2]])

# Move Arm 1 above the grasp point and descend to grasp the handle
goto_pose_arm1(arm1_handover_pos, q_arm1_open_y, z_approach=0.12)
close_gripper_arm1()

# 7. Release Arm 0 and retract safely without colliding
open_gripper_arm0()

# Lift Arm 0 straight up first to clear the hammer before retracting in X
arm0_retract_up = np.array([arm0_handover_pos[0], arm0_handover_pos[1], handover_z + 0.12])
goto_pose_arm0(arm0_retract_up, q_arm0_open_y)

# Retract Arm 0 back toward its starting side
arm0_home = np.array([0.45, 0.0, handover_z + 0.12])
goto_pose_arm0(arm0_home, q_arm0_open_y)