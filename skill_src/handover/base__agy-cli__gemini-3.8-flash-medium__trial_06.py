# Code block 0
import numpy as np

# Quaternions from problem specification
quat_arm0_down_x = np.array([0.0, 0.70710678, 0.70710678, 0.0])  # Gripper facing down, opening along X
quat_arm0_down_y = np.array([0.0, 1.0, 0.0, 0.0])                 # Gripper facing down, opening along Y
quat_arm1_down_y = np.array([0.0, 0.0, 1.0, 0.0])                 # Arm1 facing down, opening along Y

# Ensure both grippers are open initially
open_gripper_arm0()
open_gripper_arm1()

# Step 1: Get hammer handle center pose
hammer_pos, _ = get_hammer_pose()

# Grasp closer to the hammer head (-Y direction) so that after rotating,
# sufficient handle length extends toward Arm 1 (+X direction) for a collision-free grasp
grasp_pos_arm0 = hammer_pos.copy()
grasp_pos_arm0[1] -= 0.045

# Step 2: Approach and grasp the hammer with Arm 0
goto_pose_arm0(grasp_pos_arm0, quat_arm0_down_x, z_approach=0.10)
close_gripper_arm0()

# Step 3: Decomposed motion - Lift hammer straight up to clear the table surface
lift_z = 0.25
lift_pos_arm0 = grasp_pos_arm0.copy()
lift_pos_arm0[2] = lift_z
goto_pose_arm0(lift_pos_arm0, quat_arm0_down_x)

# Step 4: Decomposed motion - Rotate hammer in place
# Rotating from quat_arm0_down_x to quat_arm0_down_y turns the hammer by -90 deg around Z,
# orienting the handle along +X (pointing toward Arm 1) and the head toward -X
goto_pose_arm0(lift_pos_arm0, quat_arm0_down_y)

# Step 5: Decomposed motion - Translate Arm 0 horizontally to handover waypoint
# Midpoint between arms (approx 0.44 and 1.18) is ~0.81
handover_z = 0.175  # Must be between 0.15 and 0.20
handover_x_arm0 = 0.73
handover_pos_arm0_high = np.array([handover_x_arm0, 0.0, lift_z])
goto_pose_arm0(handover_pos_arm0_high, quat_arm0_down_y)

# Lower Arm 0 to valid handover height (0.15 < z < 0.20)
handover_pos_arm0 = np.array([handover_x_arm0, 0.0, handover_z])
goto_pose_arm0(handover_pos_arm0, quat_arm0_down_y)

# Step 6: Move Arm 1 to grasp the exposed hammer handle
# Grasp at x = 0.825 gives 9.5 cm buffer from Arm 0 (> 8 cm requirement)
# and lands reliably on the handle segment extending toward +X
handover_x_arm1 = 0.825
pre_grasp_pos_arm1 = np.array([handover_x_arm1, 0.0, lift_z])
grasp_pos_arm1 = np.array([handover_x_arm1, 0.0, handover_z])

# Orient and position Arm 1 above handover grasp point
goto_pose_arm1(pre_grasp_pos_arm1, quat_arm1_down_y)

# Descend to grasp position
goto_pose_arm1(grasp_pos_arm1, quat_arm1_down_y)

# Step 7: Complete handover
close_gripper_arm1()
open_gripper_arm0()

# Step 8: Retract Arm 0 safely away from Arm 1
retract_pos_arm0 = np.array([0.55, 0.0, handover_z])
goto_pose_arm0(retract_pos_arm0, quat_arm0_down_y)