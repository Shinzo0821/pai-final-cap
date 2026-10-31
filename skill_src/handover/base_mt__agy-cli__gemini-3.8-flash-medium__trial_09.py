# Code block 0
import numpy as np

# 1. Initialize grippers: ensure both grippers are open before approach
open_gripper_arm0()
open_gripper_arm1()

# 2. Get the hammer handle center pose
hammer_pos, _ = get_hammer_pose()

# Reference quaternions:
# Arm0 facing down, opening along X (clamps along X to grasp Y-aligned hammer):
q_arm0_pick = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down, opening along Y (after 90-degree yaw rotation):
q_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, opening along Y (clamps along Y to grasp X-aligned hammer):
q_arm1_handover = np.array([0.0, 0.0, 1.0, 0.0])

# Grasp hammer handle towards the head side (-Y offset from handle center)
# Handle length is 0.15m to 0.25m (half-length >= 0.075m).
# An offset of -0.04m stays safely on the handle while leaving ample handle space (+X) for Arm 1.
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] - 0.04, hammer_pos[2]])

# 3. Arm 0 approaches and grasps the hammer with top-down approach
goto_pose_arm0(grasp_pos_arm0, q_arm0_pick, z_approach=0.10)
close_gripper_arm0()

# 4. Decompose motion into stepwise vertical lift, rotation, and translation:
# Step A: Lift vertically to target handover height (z in [0.15, 0.20])
lift_z = 0.175
lift_pos_arm0 = np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], lift_z])
goto_pose_arm0(lift_pos_arm0, q_arm0_pick)

# Step B: Rotate hammer 90 degrees around Z axis so handle points along +X (towards Arm 1)
goto_pose_arm0(lift_pos_arm0, q_arm0_handover)

# Step C: Translate Arm 0 to handover position near the midpoint of initial gripper positions
# Midpoint between x=0.44 and x=1.18 is x=0.81.
# Maintain a 9cm (> 8cm minimum) buffer between grippers:
# Arm0 at x = 0.765, Arm1 at x = 0.855 (midpoint = 0.81).
arm0_handover_pos = np.array([0.765, 0.0, lift_z])
goto_pose_arm0(arm0_handover_pos, q_arm0_handover)

# 5. Arm 1 approaches handover pose from above along Z
arm1_handover_pos = np.array([0.855, 0.0, lift_z])
goto_pose_arm1(arm1_handover_pos, q_arm1_handover, z_approach=0.10)

# 6. Arm 1 grasps the hammer handle
close_gripper_arm1()

# 7. Arm 0 releases the hammer and retracts to complete handover
open_gripper_arm0()
arm0_retract_pos = np.array([0.65, 0.0, lift_z])
goto_pose_arm0(arm0_retract_pos, q_arm0_handover)