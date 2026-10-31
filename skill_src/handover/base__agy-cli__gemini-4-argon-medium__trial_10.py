# Code block 0
import numpy as np

# 1. Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, _ = get_hammer_pose()

# Reference quaternions (WXYZ)
# Arm0 facing down, fingers opening along X-axis (good for grasping a handle aligned along Y-axis)
q_arm0_open_x = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down, fingers opening along Y-axis (rotates hammer by 90 deg around Z so handle aligns along X-axis)
q_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, fingers opening along Y-axis (good for grasping a handle aligned along X-axis)
q_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# 2. Pick up the hammer with Arm 0
# The hammer initially lies along the Y-axis (+Y is handle end, -Y is head).
# Grasp slightly toward the head (-Y from handle center) so that when rotated toward +X,
# the handle extends toward Arm 1 (+X) with plenty of room (>8cm buffer) for Arm 1 to grasp.
grasp_offset_y = -0.04
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] + grasp_offset_y, hammer_pos[2]])

# Approach from above and grasp
goto_pose_arm0(grasp_pos_arm0, q_arm0_open_x, z_approach=0.12)
close_gripper_arm0()

# 3. Lift the hammer up to a safe height (must end up with hammer z in [0.15, 0.20] during handover)
handover_z = 0.175
lift_pos_arm0 = np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], handover_z])
goto_pose_arm0(lift_pos_arm0, q_arm0_open_x)

# 4. Rotate the hammer in place so the handle points along +X toward Arm 1.
# Going from q_arm0_open_x [0, 0.707, 0.707, 0] to q_arm0_open_y [0, 1, 0, 0] rotates
# the gripper (and hammer) by -90 degrees around the world Z-axis, mapping +Y (handle) to +X (toward Arm 1).
goto_pose_arm0(lift_pos_arm0, q_arm0_open_y)

# 5. Translate Arm 0 to the handover location near the midpoint of the two arms (x ~ 0.81, y = 0.0).
# Since Arm 0 holds the hammer at grasp_offset_y (-0.04m from handle center),
# placing Arm 0 at x = 0.76 puts the handle center at x = 0.80 and the handle tip around x = 0.88 to 0.93.
handover_pos_arm0 = np.array([0.76, 0.0, handover_z])
goto_pose_arm0(handover_pos_arm0, q_arm0_open_y)

# Check actual hammer pose at handover to ensure precision
current_hammer_pos, _ = get_hammer_pose()

# 6. Move Arm 1 to grasp the hammer handle on the +X side of the handle.
# Keep at least 8cm buffer between Arm 0 (at x = 0.76) and Arm 1: place Arm 1 at x = 0.85 (9cm separation).
# Use current_hammer_pos[2] (or handover_z) so we align with the handle height.
handover_pos_arm1 = np.array([0.85, current_hammer_pos[1], current_hammer_pos[2]])

# Move Arm 1 to handover position from above using z_approach to avoid sweeping into the hammer
goto_pose_arm1(handover_pos_arm1, q_arm1_open_y, z_approach=0.12)

# Grasp the hammer handle with Arm 1
close_gripper_arm1()

# 7. Release the hammer from Arm 0 and retract Arm 0 safely to avoid collisions
open_gripper_arm0()

# Retract Arm 0 upwards first, then back toward its home side
retract_up_arm0 = np.array([handover_pos_arm0[0], handover_pos_arm0[1], handover_z + 0.12])
goto_pose_arm0(retract_up_arm0, q_arm0_open_y)

retract_back_arm0 = np.array([0.50, 0.0, handover_z + 0.12])
goto_pose_arm0(retract_back_arm0, q_arm0_open_y)