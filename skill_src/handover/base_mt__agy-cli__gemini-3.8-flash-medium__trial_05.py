# Code block 0
import numpy as np

# Open both grippers before starting manipulation
open_gripper_arm0()
open_gripper_arm1()

# Define reference quaternions [w, x, y, z]
# Arm 0 facing down, opening along X-axis (to grasp hammer lying along Y-axis)
q_arm0_pick = np.array([0.0, 0.70710678, 0.70710678, 0.0])
# Arm 0 facing down, opening along Y-axis (after 90-degree yaw rotation)
q_arm0_hold = np.array([0.0, 1.0, 0.0, 0.0])
# Arm 1 facing down, opening along Y-axis (to grasp handle aligned along X-axis)
q_arm1_grasp = np.array([0.0, 0.0, 1.0, 0.0])

# Retrieve hammer pose (middle of handle)
hammer_pos, _ = get_hammer_pose()

# Handle length is between 0.15m and 0.25m (half-length >= 0.075m).
# Grasp 0.05m towards the head (-Y) so Arm 0 is securely on the handle,
# leaving room for Arm 1 to grasp 0.05m towards the tip (+X after rotation).
# This gives a 0.10m separation between grippers (exceeding the 8cm buffer).
arm0_pick_pos = hammer_pos.copy()
arm0_pick_pos[1] -= 0.05

# Move Arm 0 to grasp position with a vertical approach to avoid disturbing the hammer
goto_pose_arm0(arm0_pick_pos, q_arm0_pick, z_approach=0.10)
close_gripper_arm0()

# Lift hammer vertically to handover height (z = 0.18m, within [0.15m, 0.20m])
lift_pos = arm0_pick_pos.copy()
lift_pos[2] = 0.18
goto_pose_arm0(lift_pos, q_arm0_pick)

# Decompose movement: rotate in place to align hammer along X-axis
# Handle now points toward Arm 1 (+X) and head points toward Arm 0 (-X)
goto_pose_arm0(lift_pos, q_arm0_hold)

# Handover midpoint between Arm0 (0.44) and Arm1 (1.18) is x = 0.81
# With handle center at x = 0.81, Arm 0 (-0.05m) is at x = 0.76 and Arm 1 (+0.05m) is at x = 0.86
arm0_handover_pos = np.array([0.76, 0.0, 0.18])
arm1_handover_pos = np.array([0.86, 0.0, 0.18])

# Translate Arm 0 to handover position
goto_pose_arm0(arm0_handover_pos, q_arm0_hold)

# Arm 1 approaches from above to grasp the handle at x = 0.86
goto_pose_arm1(arm1_handover_pos, q_arm1_grasp, z_approach=0.10)

# Securely grasp handle with Arm 1 before Arm 0 releases to prevent dropping in the gap
close_gripper_arm1()
open_gripper_arm0()

# Retract Arm 0 safely away from Arm 1 and the hammer
arm0_retract_pos = np.array([0.60, 0.0, 0.18])
goto_pose_arm0(arm0_retract_pos, q_arm0_hold)