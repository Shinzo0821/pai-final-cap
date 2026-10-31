# Code block 0
import numpy as np

# 1. Initialize grippers to open state
open_gripper_arm0()
open_gripper_arm1()

# Reference orientations given in specification
# Arm 0 facing down, opening along X-axis (straddles the Y-aligned hammer)
q_arm0_pickup = np.array([0.0, 0.70710678, 0.70710678, 0.0])
# Arm 0 facing down, opening along Y-axis (rotates hammer to align along X-axis toward Arm 1)
q_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm 1 facing down, opening along Y-axis (straddles the X-aligned hammer)
q_arm1_handover = np.array([0.0, 0.0, 1.0, 0.0])

# 2. Query initial hammer pose
# The hammer lies flat on the table, aligned along Y-axis with head toward -Y and handle toward +Y.
hammer_pos, _ = get_hammer_pose()

# Grasp closer to the hammer head along the handle (-Y offset from handle center)
# Handle length is 0.15m - 0.25m, so -0.045m offset stays firmly on the handle while leaving room for Arm 1.
grasp0_pos = np.array([hammer_pos[0], hammer_pos[1] - 0.045, hammer_pos[2]])

# 3. Arm 0 approach and grasp
# Approach from 10cm above along Z to ensure safe downward approach
goto_pose_arm0(grasp0_pos, q_arm0_pickup, z_approach=0.10)
close_gripper_arm0()

# 4. Lift vertically to clear the table
pos_arm0_lifted = np.array([grasp0_pos[0], grasp0_pos[1], 0.25])
goto_pose_arm0(pos_arm0_lifted, q_arm0_pickup)

# 5. Rotate Arm 0 in-place
# Decomposing motion: rotate first to align hammer handle along +X toward Arm 1
goto_pose_arm0(pos_arm0_lifted, q_arm0_handover)

# 6. Move Arm 0 stepwise to handover location
# Handover midpoint between x=0.44 and x=1.18 is x=0.81.
# Target z for hammer during handover must be between 0.15 and 0.20 -> z = 0.175.
# Arm 0 holds handle at x = 0.76, orienting the handle toward +X.
pos_arm0_high = np.array([0.76, 0.0, 0.25])
pos_arm0_handover = np.array([0.76, 0.0, 0.175])

# Translate in XY at safe elevation, then lower to target handover height
goto_pose_arm0(pos_arm0_high, q_arm0_handover)
goto_pose_arm0(pos_arm0_handover, q_arm0_handover)

# 7. Arm 1 moves stepwise to grasp the handle
# Grasp point at x = 0.86 provides 10cm separation (> 8cm minimum buffer) from Arm 0.
# The handle extends from x=0.76 to at least x=0.88, so x=0.86 grasps securely on the handle.
pos_arm1_prep = np.array([1.00, 0.0, 0.25])
pos_arm1_high = np.array([0.86, 0.0, 0.25])
pos_arm1_handover = np.array([0.86, 0.0, 0.175])

goto_pose_arm1(pos_arm1_prep, q_arm1_handover)
goto_pose_arm1(pos_arm1_high, q_arm1_handover)
goto_pose_arm1(pos_arm1_handover, q_arm1_handover)

# 8. Complete handover transfer
close_gripper_arm1()
open_gripper_arm0()

# Retract Arm 0 safely away from Arm 1
pos_arm0_retract = np.array([0.60, 0.0, 0.25])
goto_pose_arm0(pos_arm0_retract, q_arm0_handover)