# Code block 0
import numpy as np

# 1. Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, _ = get_hammer_pose()

# Reference orientations:
# Arm 0 facing down, opening along X-axis (to grasp hammer initially aligned along Y-axis)
quat_arm0_open_x = np.array([0.0, 0.707, 0.707, 0.0])
# Arm 0 facing down, opening along Y-axis (after rotating 90 degrees around Z so hammer aligns along X-axis)
quat_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm 1 facing down, opening along Y-axis (to grasp hammer when aligned along X-axis)
quat_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Ensure both grippers are open initially
open_gripper_arm0()
open_gripper_arm1()

# 2. Pick up the hammer with Arm 0
# The hammer initially lies flat on the table aligned along the Y-axis:
# Handle is toward +Y, hammer head is toward -Y.
# get_hammer_pose() gives the middle of the handle.
# Since handle length is between 0.15m and 0.25m, if Arm 0 grasps slightly toward the head (-Y offset from handle center),
# it leaves the rest of the handle (+Y side from grasp point) free for Arm 1 to grasp during handover!
# Furthermore, when Arm 0 rotates from [0, 0.707, 0.707, 0] to [0, 1, 0, 0] (a -90 deg rotation around Z),
# the +Y direction rotates into the +X direction (pointing directly toward Arm 1!).
grasp_offset = -0.04  # 4cm toward the head (-Y) from the handle center
arm0_pick_pos = np.array([hammer_pos[0], hammer_pos[1] + grasp_offset, hammer_pos[2]])

# Approach from above and grasp with Arm 0
goto_pose_arm0(arm0_pick_pos, quat_arm0_open_x, z_approach=0.12)
close_gripper_arm0()

# 3. Lift the hammer up to handover height (z between 0.15 and 0.20, choose 0.18)
handover_z = 0.18
arm0_lift_pos = np.array([arm0_pick_pos[0], arm0_pick_pos[1], handover_z])
goto_pose_arm0(arm0_lift_pos, quat_arm0_open_x)

# 4. Decompose movement into rotation and translation:
# First rotate Arm 0 in place so that the hammer handle points toward +X (toward Arm 1)
# Moving from quat_arm0_open_x [0, 0.707, 0.707, 0] to quat_arm0_open_y [0, 1, 0, 0]
# rotates the gripper by -90 degrees around the world Z-axis, bringing the +Y handle end to +X.
goto_pose_arm0(arm0_lift_pos, quat_arm0_open_y)

# 5. Translate Arm 0 to the handover position near the midpoint (midpoint X ~ (0.44 + 1.18)/2 = 0.81)
# Keep Arm 0 slightly to the left of the midpoint so the handle extends across the midpoint toward Arm 1.
# We check the updated hammer pose after rotation to precisely know the offset between Arm 0 and handle center,
# or use known geometry: after -90 deg Z rotation, the handle center is at +0.04m in X relative to Arm 0,
# and the free end of the handle extends at least another 0.075m to 0.125m in +X.
handover_y = 0.0
arm0_handover_x = 0.75
arm0_handover_pos = np.array([arm0_handover_x, handover_y, handover_z])
goto_pose_arm0(arm0_handover_pos, quat_arm0_open_y)

# Read the current hammer pose at handover to verify exact handle center position and height
curr_hammer_pos, _ = get_hammer_pose()

# Adjust Arm 0 Z slightly if needed to ensure curr_hammer_pos[2] is strictly within [0.15, 0.20]
target_hammer_z = 0.175
z_correction = target_hammer_z - curr_hammer_pos[2]
if abs(z_correction) > 0.005:
    arm0_handover_pos[2] += z_correction
    goto_pose_arm0(arm0_handover_pos, quat_arm0_open_y)
    curr_hammer_pos, _ = get_hammer_pose()

# 6. Move Arm 1 to grasp the hammer handle
# Maintain at least an 8cm buffer (e.g. 0.095m) between Arm 0 gripper and Arm 1 gripper along X-axis.
# Since Arm 0 grasps at -0.04m from handle center (now along X), a +0.095m X separation from Arm 0
# places Arm 1 at +0.055m from the handle center (well on the handle even for the shortest 0.15m handle,
# whose end is at +0.075m from the center).
arm1_grasp_x = max(arm0_handover_pos[0] + 0.095, curr_hammer_pos[0] + 0.045)
arm1_grasp_pos = np.array([arm1_grasp_x, curr_hammer_pos[1], arm0_handover_pos[2]])

# First orient and position Arm 1 safely above the grasp point, then descend and grasp
goto_pose_arm1(arm1_grasp_pos, quat_arm1_open_y, z_approach=0.12)
close_gripper_arm1()

# 7. Release Arm 0 and retract safely without colliding
open_gripper_arm0()

# Retract Arm 0 upwards first, then back toward its starting side
arm0_retract_up = np.array([arm0_handover_pos[0], arm0_handover_pos[1], arm0_handover_pos[2] + 0.12])
goto_pose_arm0(arm0_retract_up, quat_arm0_open_y)

arm0_home_pos = np.array([0.45, 0.0, 0.30])
goto_pose_arm0(arm0_home_pos, quat_arm0_open_y)