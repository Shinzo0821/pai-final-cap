# Code block 0
import numpy as np

# 1. Retrieve initial hammer handle pose
hammer_pos, _ = get_hammer_pose()

# Reference quaternions
# Arm0 facing down, opening along X (to grasp hammer lying along Y)
q_arm0_pick = np.array([0.0, 0.70710678, 0.70710678, 0.0])
# Arm0 facing down, opening along Y (after 90 deg rotation, hammer aligned along X)
q_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, opening along Y (to grasp hammer aligned along X)
q_arm1_handover = np.array([0.0, 0.0, 1.0, 0.0])

# Handover height must be between 0.15 and 0.20
handover_z = 0.175

# Ensure both grippers are open
open_gripper_arm0()
open_gripper_arm1()

# 2. Arm0 approaches hammer: grasp slightly toward the head (-Y direction from center)
# so there is sufficient handle length left for Arm1 to grasp with >8cm buffer.
grasp_pos = hammer_pos.copy()
grasp_pos[1] -= 0.05

goto_pose_arm0(grasp_pos, q_arm0_pick, z_approach=0.10)
close_gripper_arm0()

# 3. Lift vertically first to safely clear table surface
lift_pos = grasp_pos.copy()
lift_pos[2] = handover_z
goto_pose_arm0(lift_pos, q_arm0_pick)

# 4. Decompose movement: rotate in place so hammer aligns along X-axis
# Handle now points toward +X (toward Arm1), head toward -X
goto_pose_arm0(lift_pos, q_arm0_handover)

# 5. Translate Arm0 to handover waypoint near the midpoint (x ~ 0.81)
# With Arm0 at x = 0.76, the center of handle is at x = 0.81
handover_arm0 = np.array([0.76, 0.0, handover_z])
goto_pose_arm0(handover_arm0, q_arm0_handover)

# 6. Arm1 moves to grasp the handle at x = 0.85 (9cm buffer > 8cm minimum)
# Approach vertically from above to avoid collision with hammer or Arm0
handover_arm1 = np.array([0.85, 0.0, handover_z])
goto_pose_arm1(handover_arm1, q_arm1_handover, z_approach=0.10)

# 7. Complete handover: Arm1 grasps handle, Arm0 releases and retracts safely
close_gripper_arm1()
open_gripper_arm0()

# Retract Arm0 upward and backward to safe position
retract_arm0 = np.array([0.60, 0.0, 0.25])
goto_pose_arm0(retract_arm0, q_arm0_handover)