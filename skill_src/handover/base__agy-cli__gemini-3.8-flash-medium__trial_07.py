# Code block 0
import numpy as np

# 1. Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# 2. Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, _ = get_hammer_pose()

# Reference quaternions
# Arm 0 facing down opening along X-axis (to grasp hammer lying along Y-axis)
q_arm0_pickup = np.array([0.0, 0.707, 0.707, 0.0])
# Arm 0 facing down opening along Y-axis (after rotation, hammer aligned along X-axis)
q_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm 1 facing down opening along Y-axis (to grasp hammer handle aligned along X-axis)
q_arm1_handover = np.array([0.0, 0.0, 1.0, 0.0])

# 3. Arm 0 grasps hammer handle
# Handle length is 0.15m-0.25m; grasp with -0.045m offset along Y (towards head) so it remains safely on handle
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] - 0.045, hammer_pos[2]])
goto_pose_arm0(grasp_pos_arm0, q_arm0_pickup, z_approach=0.10)
close_gripper_arm0()

# 4. Lift vertically to clear the table
lift_pos_arm0 = np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], 0.25])
goto_pose_arm0(lift_pos_arm0, q_arm0_pickup)

# 5. Rotate hammer stepwise in place so handle points along +X toward Arm 1
goto_pose_arm0(lift_pos_arm0, q_arm0_handover)

# 6. Move Arm 0 to handover waypoint and descend to target z in [0.15, 0.20] (z = 0.175)
# Midpoint of initial arm positions (0.44 and 1.18) is x = 0.81
handover_pos_arm0 = np.array([0.765, 0.0, 0.175])
waypoint_arm0 = np.array([0.765, 0.0, 0.25])
goto_pose_arm0(waypoint_arm0, q_arm0_handover)
goto_pose_arm0(handover_pos_arm0, q_arm0_handover)

# 7. Arm 1 approaches from above and grasps the handle
# Target position is at x = 0.855 (9cm separation between grippers, satisfying >8cm buffer)
grasp_pos_arm1 = np.array([0.855, 0.0, 0.175])
goto_pose_arm1(grasp_pos_arm1, q_arm1_handover, z_approach=0.10)
close_gripper_arm1()

# 8. Release Arm 0 to complete handover
open_gripper_arm0()