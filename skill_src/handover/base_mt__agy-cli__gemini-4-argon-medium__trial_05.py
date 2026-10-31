# Code block 0
import numpy as np

# 1. Define reference orientations (WXYZ quaternions)
# Arm 0 facing down, opening along X-axis (for grasping hammer aligned with Y-axis)
q_arm0_grasp = np.array([0.0, 0.707, 0.707, 0.0])
# Arm 0 facing down, opening along Y-axis (rotates hammer +90 deg so handle points along +X toward Arm 1)
q_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm 1 facing down, opening along Y-axis (for grasping hammer handle aligned with X-axis)
q_arm1_handover = np.array([0.0, 0.0, 1.0, 0.0])

# 2. Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# 3. Get initial hammer handle center pose
hammer_pos, _ = get_hammer_pose()

# Grasp offset along the handle:
# Minimum handle length is 0.15m (half-length 0.075m).
# Grasping 0.045m toward the head (-Y) and +0.045m toward the tip (+X after rotation)
# keeps both grippers well on the handle while maintaining a 0.09m (> 8cm) buffer between grippers.
arm0_grasp_offset = 0.045
arm1_grasp_offset = 0.045

# 4. Move Arm 0 to pick up the hammer on the -Y side of the handle center (closer to the head)
grasp_pos_arm0 = np.array([
    hammer_pos[0],
    hammer_pos[1] - arm0_grasp_offset,
    hammer_pos[2]
])
goto_pose_arm0(grasp_pos_arm0, q_arm0_grasp, z_approach=0.10)
close_gripper_arm0()

# 5. Lift the hammer vertically first to avoid table collisions (target Z in [0.15, 0.20])
handover_z = 0.175
lift_pos_arm0 = np.array([
    grasp_pos_arm0[0],
    grasp_pos_arm0[1],
    handover_z
])
goto_pose_arm0(lift_pos_arm0, q_arm0_grasp)

# 6. Rotate the hammer in place so the handle points toward +X (toward Arm 1)
goto_pose_arm0(lift_pos_arm0, q_arm0_handover)

# 7. Translate Arm 0 to the handover region near the midpoint (x ~ 0.81, y = 0.0)
# With Arm 0 at x = 0.765, the handle center will be at x ~ 0.81 and Arm 1 will grasp at x ~ 0.855
handover_pos_arm0 = np.array([0.765, 0.0, handover_z])
goto_pose_arm0(handover_pos_arm0, q_arm0_handover)

# 8. Query the current hammer handle center pose to ensure accurate Z height and grasp alignment
current_hammer_pos, _ = get_hammer_pose()
z_error = handover_z - current_hammer_pos[2]
if abs(z_error) > 0.005:
    handover_pos_arm0[2] += z_error
    goto_pose_arm0(handover_pos_arm0, q_arm0_handover)
    current_hammer_pos, _ = get_hammer_pose()

# 9. Move Arm 1 to grasp the exposed +X end of the hammer handle using a safe Z approach
grasp_pos_arm1 = np.array([
     max(current_hammer_pos[0] + arm1_grasp_offset, handover_pos_arm0[0] + 0.09),
    current_hammer_pos[1],
    current_hammer_pos[2]
])

# Pre-position Arm 1 safely above the handover point before descending
pre_grasp_pos_arm1 = np.array([
    grasp_pos_arm1[0],
    grasp_pos_arm1[1],
    grasp_pos_arm1[2] + 0.12
])
goto_pose_arm1(pre_grasp_pos_arm1, q_arm1_handover)
goto_pose_arm1(grasp_pos_arm1, q_arm1_handover)
close_gripper_arm1()

# 10. Release Arm 0 gripper and retract Arm 0 safely away from the hammer and Arm 1
open_gripper_arm0()

retract_up_arm0 = np.array([
    handover_pos_arm0[0],
    handover_pos_arm0[1],
    handover_pos_arm0[2] + 0.12
])
goto_pose_arm0(retract_up_arm0, q_arm0_handover)

retract_home_arm0 = np.array([0.45, 0.0, handover_pos_arm0[2] + 0.12])
goto_pose_arm0(retract_home_arm0, q_arm0_handover)