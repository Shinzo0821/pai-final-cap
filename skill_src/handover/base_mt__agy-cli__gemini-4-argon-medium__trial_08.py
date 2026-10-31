# Code block 0
import numpy as np

# 1. Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, _ = get_hammer_pose()

# Reference quaternions (WXYZ)
# Arm0 facing down, fingers opening along X-axis (good for grasping handle aligned along Y-axis)
quat_arm0_open_x = np.array([0.0, 0.70710678, 0.70710678, 0.0])
# Arm0 facing down, fingers opening along Y-axis (rotates hammer so handle aligns with X-axis)
quat_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, fingers opening along Y-axis (good for grasping handle aligned along X-axis)
quat_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Ensure both grippers are open initially
open_gripper_arm0()
open_gripper_arm1()

# 2. Pick up the hammer with Arm 0
# The hammer initially lies along the Y-axis (+Y handle, -Y head).
# Grasp near the head (-Y side of the handle center) so plenty of handle (+Y side) is free for Arm 1.
# Since minimum handle length is 0.15m (half-length 0.075m), -0.04m from center is safely on the handle near the head.
grasp_arm0_pos = np.array([hammer_pos[0], hammer_pos[1] - 0.04, hammer_pos[2]])
goto_pose_arm0(grasp_arm0_pos, quat_arm0_open_x, z_approach=0.12)
close_gripper_arm0()

# 3. Lift the hammer to a safe handover height (hammer z must be between 0.15 and 0.20)
handover_z = 0.175
lift_pos = np.array([grasp_arm0_pos[0], grasp_arm0_pos[1], handover_z])
goto_pose_arm0(lift_pos, quat_arm0_open_x)

# 4. Rotate the hammer in-place so the handle points towards Arm 1 (+X direction)
# Rotating from [0, 0.707, 0.707, 0] to [0, 1, 0, 0] rotates the gripper +90 deg around Z (from +X to +Y),
# which rotates the +Y handle to point along +X towards Arm 1.
goto_pose_arm0(lift_pos, quat_arm0_open_y)

# 5. Translate Arm 0 to the handover location near the midpoint (midpoint x ~ 0.81)
# Since Arm 0 is holding at -0.04m from handle center, putting Arm 0 at x = 0.76 places handle center at ~0.80
# and the free handle extending towards +X (up to ~0.875 - 0.925).
handover_arm0_pos = np.array([0.76, 0.0, handover_z])
goto_pose_arm0(handover_arm0_pos, quat_arm0_open_y)

# 6. Check actual hammer pose at handover to accurately target the handle with Arm 1
current_hammer_pos, _ = get_hammer_pose()

# Arm 1 grasps the handle on the +X side of the handle center.
# Ensure at least an 8cm (0.08m) buffer between Arm 0 (x=0.76) and Arm 1 (x=0.85 -> 9cm buffer).
# At x = 0.85, it is ~0.05m from the handle center (0.80), which is safely on the handle even for the shortest 0.15m handle.
handover_arm1_x = max(handover_arm0_pos[0] + 0.09, current_hammer_pos[0] + 0.04)
handover_arm1_pos = np.array([handover_arm1_x, current_hammer_pos[1], current_hammer_pos[2]])

# Move Arm 1 to grasp the handle using z_approach to avoid sweeping into the hammer
goto_pose_arm1(handover_arm1_pos, quat_arm1_open_y, z_approach=0.12)
close_gripper_arm1()

# 7. Release Arm 0 and retract it safely away to avoid collisions
open_gripper_arm0()

# Move Arm 0 straight up first to clear the hammer
retract_up_arm0 = np.array([handover_arm0_pos[0], handover_arm0_pos[1], handover_z + 0.12])
goto_pose_arm0(retract_up_arm0, quat_arm0_open_y)

# Translate Arm 0 back towards its starting side
retract_back_arm0 = np.array([0.44, 0.0, handover_z + 0.12])
goto_pose_arm0(retract_back_arm0, quat_arm0_open_y)

# 8. Retract Arm 1 with the hammer to its side while maintaining handover height
retract_arm1 = np.array([1.05, 0.0, handover_z])
goto_pose_arm1(retract_arm1, quat_arm1_open_y)

# Code block 1
import numpy as np

# 1. Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, hammer_quat = get_hammer_pose()
print(f"Initial hammer pos: {hammer_pos}, quat: {hammer_quat}")

# Reference quaternions (WXYZ)
quat_arm0_open_x = np.array([0.0, 0.70710678, 0.70710678, 0.0])
quat_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])
quat_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Ensure both grippers are open initially
open_gripper_arm0()
open_gripper_arm1()

# 2. Pick up the hammer with Arm 0
# The hammer initially lies along the Y-axis (+Y handle, -Y head).
# Grasp near the head (-Y side of the handle center) so the +Y side of the handle is free for Arm 1.
grasp_arm0_pos = np.array([hammer_pos[0], hammer_pos[1] - 0.04, hammer_pos[2]])
goto_pose_arm0(grasp_arm0_pos, quat_arm0_open_x, z_approach=0.12)
close_gripper_arm0()

# 3. Lift the hammer to handover height (between 0.15 and 0.20)
handover_z = 0.175
lift_pos = np.array([grasp_arm0_pos[0], grasp_arm0_pos[1], handover_z])
goto_pose_arm0(lift_pos, quat_arm0_open_x)
lifted_hammer_pos, _ = get_hammer_pose()
print(f"After lift hammer pos: {lifted_hammer_pos}")

# 4. Rotate the hammer in-place so the handle points towards Arm 1 (+X direction)
goto_pose_arm0(lift_pos, quat_arm0_open_y)
rotated_hammer_pos, _ = get_hammer_pose()
print(f"After rotate hammer pos: {rotated_hammer_pos}")

# 5. Translate Arm 0 to the handover location near the midpoint (midpoint x ~ 0.81)
handover_arm0_pos = np.array([0.76, 0.0, handover_z])
goto_pose_arm0(handover_arm0_pos, quat_arm0_open_y)

# 6. Check actual hammer pose at handover to accurately target the handle with Arm 1
current_hammer_pos, _ = get_hammer_pose()
print(f"At handover hammer pos: {current_hammer_pos}")

# Arm 1 grasps the handle on the +X side of the handle center, keeping >= 8cm buffer from Arm 0
handover_arm1_x = max(handover_arm0_pos[0] + 0.09, current_hammer_pos[0] + 0.04)
handover_arm1_pos = np.array([handover_arm1_x, current_hammer_pos[1], current_hammer_pos[2]])
print(f"Arm 1 target grasp pos: {handover_arm1_pos}")

# Move Arm 1 to grasp the handle using z_approach
goto_pose_arm1(handover_arm1_pos, quat_arm1_open_y, z_approach=0.12)
close_gripper_arm1()

# 7. Release Arm 0 and retract it safely away to avoid collisions
open_gripper_arm0()

retract_up_arm0 = np.array([handover_arm0_pos[0], handover_arm0_pos[1], handover_z + 0.12])
goto_pose_arm0(retract_up_arm0, quat_arm0_open_y)

retract_back_arm0 = np.array([0.44, 0.0, handover_z + 0.12])
goto_pose_arm0(retract_back_arm0, quat_arm0_open_y)

# 8. Move Arm 1 slightly back while keeping height within handover range
retract_arm1 = np.array([0.95, 0.0, handover_z])
goto_pose_arm1(retract_arm1, quat_arm1_open_y)

final_hammer_pos, _ = get_hammer_pose()
print(f"Final hammer pos: {final_hammer_pos}")