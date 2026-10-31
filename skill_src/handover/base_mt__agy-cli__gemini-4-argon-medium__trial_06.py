# Code block 0
import numpy as np

# 1. Get initial hammer pose (position of the middle of the handle)
hammer_pos, _ = get_hammer_pose()

# Reference orientations (w, x, y, z)
# Arm0 facing down, gripper fingers opening along X-axis (good for grasping handle aligned with Y-axis)
quat_arm0_grasp = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down, gripper fingers opening along Y-axis (rotates hammer 90 deg around Z so handle is along X-axis)
quat_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, gripper fingers opening along Y-axis (good for grasping handle aligned with X-axis)
quat_arm1_grasp = np.array([0.0, 0.0, 1.0, 0.0])

# Ensure both grippers are open initially
open_gripper_arm0()
open_gripper_arm1()

# 2. Pick up the hammer with Arm 0
# Grasp near the head end of the handle (-Y offset from handle center) so that when rotated,
# the rest of the handle extends toward Arm 1 (+X) and leaves plenty of room (>= 8cm buffer) for Arm 1 to grasp.
grasp_offset = 0.04
arm0_pick_pos = np.array([hammer_pos[0], hammer_pos[1] - grasp_offset, hammer_pos[2]])

goto_pose_arm0(arm0_pick_pos, quat_arm0_grasp, z_approach=0.12)
close_gripper_arm0()

# 3. Lift the hammer to handover height (hammer z must be between 0.15 and 0.20)
handover_z = 0.175
arm0_lift_pos = np.array([arm0_pick_pos[0], arm0_pick_pos[1], handover_z])
goto_pose_arm0(arm0_lift_pos, quat_arm0_grasp)

# 4. Rotate Arm 0 in place so the hammer handle points toward Arm 1 (+X direction)
# Rotating from [0, 0.707, 0.707, 0] to [0, 1, 0, 0] is a -90 deg rotation around Z.
# Since Arm 0 grasped at -Y relative to the handle center, the handle center (+Y relative to grasp)
# rotates to +X relative to Arm 0's gripper, pointing directly toward Arm 1!
goto_pose_arm0(arm0_lift_pos, quat_arm0_handover)

# 5. Move Arm 0 to the handover position near the midpoint (x ~ 0.81, y = 0.0)
# Place Arm 0 at x = 0.76 so the handle center is at x ~ 0.80 and the free end extends to x ~ 0.87+.
arm0_handover_pos = np.array([0.76, 0.0, handover_z])
goto_pose_arm0(arm0_handover_pos, quat_arm0_handover)

# Read actual hammer pose during handover to get exact Z and Y, while maintaining a safe >= 9cm X-buffer from Arm 0
current_hammer_pos, _ = get_hammer_pose()
arm1_grasp_x = max(arm0_handover_pos[0] + 0.09, current_hammer_pos[0] + 0.04)
arm1_grasp_y = current_hammer_pos[1]
arm1_grasp_z = np.clip(current_hammer_pos[2], 0.16, 0.19)

arm1_handover_pos = np.array([arm1_grasp_x, arm1_grasp_y, arm1_grasp_z])

# 6. Move Arm 1 to grasp the hammer handle (using z_approach to descend safely from above)
goto_pose_arm1(arm1_handover_pos, quat_arm1_grasp, z_approach=0.12)
close_gripper_arm1()

# 7. Release Arm 0 and retract it safely away from Arm 1
open_gripper_arm0()

# Lift Arm 0 straight up first to clear the hammer head and handle before translating back
arm0_retract_up = np.array([arm0_handover_pos[0], arm0_handover_pos[1], handover_z + 0.12])
goto_pose_arm0(arm0_retract_up, quat_arm0_handover)

arm0_home = np.array([0.44, 0.0, 0.30])
goto_pose_arm0(arm0_home, quat_arm0_handover)

# Code block 1
import numpy as np

# 1. Get initial hammer pose (position of the middle of the handle)
hammer_pos, _ = get_hammer_pose()
print("Initial hammer pos:", hammer_pos)

# Reference orientations (w, x, y, z)
# Arm0 facing down, gripper fingers opening along X-axis (good for grasping handle aligned with Y-axis)
quat_arm0_grasp = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down, gripper fingers opening along Y-axis (rotates hammer 90 deg around Z so handle is along X-axis)
quat_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, gripper fingers opening along Y-axis (good for grasping handle aligned with X-axis)
quat_arm1_grasp = np.array([0.0, 0.0, 1.0, 0.0])

# Ensure both grippers are open initially
open_gripper_arm0()
open_gripper_arm1()

# 2. Pick up the hammer with Arm 0
# Grasp near the head end of the handle (-Y offset from handle center) so that when rotated,
# the rest of the handle extends toward Arm 1 (+X) and leaves plenty of room (>= 8cm buffer) for Arm 1 to grasp.
grasp_offset = 0.04
arm0_pick_pos = np.array([hammer_pos[0], hammer_pos[1] - grasp_offset, hammer_pos[2]])

goto_pose_arm0(arm0_pick_pos, quat_arm0_grasp, z_approach=0.12)
close_gripper_arm0()

# 3. Lift the hammer to handover height (hammer z must be between 0.15 and 0.20)
handover_z = 0.175
arm0_lift_pos = np.array([arm0_pick_pos[0], arm0_pick_pos[1], handover_z])
goto_pose_arm0(arm0_lift_pos, quat_arm0_grasp)

# 4. Rotate Arm 0 in place so the hammer handle points toward Arm 1 (+X direction)
# Check which way the handle rotates by moving to quat_arm0_handover and inspecting get_hammer_pose()
goto_pose_arm0(arm0_lift_pos, quat_arm0_handover)
pos_after_rot, _ = get_hammer_pose()
print("Hammer pos after rot:", pos_after_rot)

# If the handle center moved to -X relative to arm0_lift_pos[0], then [0, 1, 0, 0] rotated it +90 deg instead of -90 deg.
# In that case, [-0.0, 0.0, 1.0, 0.0] is the opposite 180-deg-rotated gripper orientation around Z!
if pos_after_rot[0] < arm0_lift_pos[0]:
    quat_arm0_handover = np.array([0.0, 0.0, 1.0, 0.0])
    goto_pose_arm0(arm0_lift_pos, quat_arm0_handover)
    pos_after_rot, _ = get_hammer_pose()
    print("Hammer pos after corrected rot:", pos_after_rot)

# 5. Move Arm 0 to the handover position near the midpoint (x ~ 0.81, y = 0.0)
# Place Arm 0 at x = 0.76 so the handle center is at x ~ 0.80 and the free end extends to x ~ 0.87+.
arm0_handover_pos = np.array([0.76, 0.0, handover_z])
goto_pose_arm0(arm0_handover_pos, quat_arm0_handover)

# Read actual hammer pose during handover to get exact Z and Y, while maintaining a safe >= 9cm X-buffer from Arm 0
current_hammer_pos, _ = get_hammer_pose()
print("Hammer pos at handover:", current_hammer_pos)

arm1_grasp_x = max(arm0_handover_pos[0] + 0.09, current_hammer_pos[0] + 0.04)
arm1_grasp_y = current_hammer_pos[1]
arm1_grasp_z = np.clip(current_hammer_pos[2], 0.16, 0.19)

arm1_handover_pos = np.array([arm1_grasp_x, arm1_grasp_y, arm1_grasp_z])
print("Arm1 target grasp pos:", arm1_handover_pos)

# 6. Move Arm 1 to grasp the hammer handle (using z_approach to descend safely from above)
goto_pose_arm1(arm1_handover_pos, quat_arm1_grasp, z_approach=0.12)
close_gripper_arm1()

# 7. Release Arm 0 and retract it safely away from Arm 1
open_gripper_arm0()

# Lift Arm 0 straight up first to clear the hammer head and handle before translating back
arm0_retract_up = np.array([arm0_handover_pos[0], arm0_handover_pos[1], handover_z + 0.12])
goto_pose_arm0(arm0_retract_up, quat_arm0_handover)

arm0_home = np.array([0.44, 0.0, 0.30])
goto_pose_arm0(arm0_home, quat_arm0_handover)

final_hammer_pos, _ = get_hammer_pose()
print("Final hammer pos:", final_hammer_pos)