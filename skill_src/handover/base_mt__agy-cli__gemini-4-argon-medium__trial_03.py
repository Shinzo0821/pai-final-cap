# Code block 0
import numpy as np

# 1. Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, _ = get_hammer_pose()

# Reference quaternions (WXYZ)
# Arm0 facing down, fingers opening along X-axis (good for grasping a handle aligned along Y-axis)
q_arm0_grasp_y = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down, fingers opening along Y-axis (rotates the grasped hammer by 90 deg around Z so handle aligns along X-axis)
q_arm0_grasp_x = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, fingers opening along Y-axis (good for grasping a handle aligned along X-axis)
q_arm1_grasp_x = np.array([0.0, 0.0, 1.0, 0.0])

# Ensure both grippers start open
open_gripper_arm0()
open_gripper_arm1()

# 2. Pick up the hammer with Arm 0
# The hammer is aligned along the Y-axis (+Y handle, -Y head).
# Grasp slightly toward -Y (closer to the hammer head) from the handle center so that when rotated
# 90 degrees clockwise ( viewed from top: +Y rotates to +X, -Y rotates to -X ), the remaining handle
# extends toward Arm 1 (+X) and there is plenty of clearance (>8cm) between the two grippers.
y_grasp_offset = -0.04
arm0_pick_pos = np.array([hammer_pos[0], hammer_pos[1] + y_grasp_offset, hammer_pos[2]])

goto_pose_arm0(arm0_pick_pos, q_arm0_grasp_y, z_approach=0.12)
close_gripper_arm0()

# 3. Lift the hammer to handover height (hammer z must be between 0.15 and 0.20)
handover_z = 0.175
arm0_lift_pos = np.array([arm0_pick_pos[0], arm0_pick_pos[1], handover_z])
goto_pose_arm0(arm0_lift_pos, q_arm0_grasp_y)

# 4. Rotate the hammer in place so the handle points along the X-axis toward Arm 1 (+X)
# Decompose rotation and translation stepwise to avoid collisions.
# Rotating from [0, 0.707, 0.707, 0] to [0, 1, 0, 0] rotates the gripper +90 deg around World Z (or -90 deg),
# aligning the hammer handle along the X-axis with the handle extending toward +X (Arm 1) and head toward -X (Arm 0).
goto_pose_arm0(arm0_lift_pos, q_arm0_grasp_x)

# 5. Move Arm 0 to the handover position near the midpoint (midpoint of 0.44 and 1.18 is ~0.81)
# Position Arm 0 at x = 0.75, y = 0.0 so the handle center is around x = 0.79 and the handle end reaches ~0.86+.
arm0_handover_pos = np.array([0.75, 0.0, handover_z])
goto_pose_arm0(arm0_handover_pos, q_arm0_grasp_x)

# Verify hammer pose at handover to adapt to the exact rotated geometry and handle length
current_hammer_pos, _ = get_hammer_pose()

# Determine which way the handle center shifted relative to Arm 0's gripper (x = 0.75)
# If current_hammer_pos[0] > 0.75, the handle extends toward +X (Arm 1).
# If current_hammer_pos[0] < 0.75, the handle extends toward -X, so we flip Arm 0 by 180 deg around Z: wait,
# quaternion [0, 1, 0, 0] vs [0, -1, 0, 0] is the same 3D rotation! Because picking at y_grasp_offset = -0.04
# puts the handle center at +0.04 relative to the gripper along the handle axis.
# From q_arm0_grasp_y = [0, 0.7071, 0.7071, 0] (X_gripper = [0, 1, 0], Y_gripper = [1, 0, 0], Z_gripper = [0, 0, -1]),
# the handle is along X_gripper ([0, 1, 0]).
# At q_arm0_grasp_x = [0, 1, 0, 0] (X_gripper = [1, 0, 0], Y_gripper = [0, -1, 0], Z_gripper = [0, 0, -1]),
# X_gripper points along +X ([1, 0, 0])! Thus the handle (+Y initially, which was +X_gripper) now points strictly along +X!

# 6. Move Arm 1 to grasp the hammer handle
# Arm 0 is at x = 0.75. To maintain at least an 8cm buffer between grippers while staying securely on the handle
# (even for the minimum 0.15m handle where handle extends from x = 0.79 - 0.075 = 0.715 to 0.79 + 0.075 = 0.865),
# Arm 1 grasps at x = 0.84 (9cm buffer from Arm 0's gripper at 0.75, and well within the handle end at >= 0.865).
arm1_grasp_x = max(0.84, current_hammer_pos[0] + 0.05)
arm1_handover_pos = np.array([arm1_grasp_x, current_hammer_pos[1], current_hammer_pos[2]])

# Move Arm 1 above the grasp point first, then descend (using z_approach)
goto_pose_arm1(arm1_handover_pos, q_arm1_grasp_x, z_approach=0.12)

# 7. Grasp the hammer with Arm 1 and release Arm 0
close_gripper_arm1()
open_gripper_arm0()

# 8. Retract Arm 0 safely away from the handover zone (upwards first, then back toward Arm 0's side)
arm0_retract_up = np.array([arm0_handover_pos[0], arm0_handover_pos[1], handover_z + 0.12])
goto_pose_arm0(arm0_retract_up, q_arm0_grasp_x)

arm0_home_pos = np.array([0.45, 0.0, handover_z + 0.12])
goto_pose_arm0(arm0_home_pos, q_arm0_grasp_x)