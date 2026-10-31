# Code block 0
import numpy as np

# Quaternions specified in the environment specification:
# Arm0 facing down opening along X-axis (used to grasp the hammer aligned along Y-axis)
q_arm0_pickup = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down opening along Y-axis (holding hammer aligned along X-axis)
q_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down opening along Y-axis (used to grasp hammer aligned along X-axis)
q_arm1_handover = np.array([0.0, 0.0, 1.0, 0.0])

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# 1. Get initial hammer handle pose
hammer_pos, _ = get_hammer_pose()

# Grasp offset: handle is aligned along Y with head toward -Y.
# Grasp 0.05m toward the head (-Y) so that the remaining handle points toward +Y (and later +X).
# With handle length >= 0.15m, 0.05m offset is safely on the handle.
grasp_pos = np.array([hammer_pos[0], hammer_pos[1] - 0.05, hammer_pos[2]])

# Move Arm0 to grasp the hammer handle, approaching from above
goto_pose_arm0(grasp_pos, q_arm0_pickup, z_approach=0.12)
close_gripper_arm0()

# 2. Lift hammer vertically (translation only) to clear the table
lift_z = 0.25
lift_pos = np.array([grasp_pos[0], grasp_pos[1], lift_z])
goto_pose_arm0(lift_pos, q_arm0_pickup)

# 3. Rotate hammer to align with X-axis (pure rotation in place)
# This rotates the handle tail toward +X (Arm1's side) and head toward -X (Arm0's side)
goto_pose_arm0(lift_pos, q_arm0_handover)

# 4. Translate Arm0 to handover position:
# Midpoint of initial positions (0.44 + 1.18) / 2 = 0.81.
# Target hammer center at x = 0.81, y = 0.0, z = 0.175 (within [0.15, 0.20]).
# Since Arm0 grasps 0.05m toward the head (-X), Arm0 end-effector target is x = 0.76.
handover_z = 0.175
arm0_handover_pos = np.array([0.76, 0.0, handover_z])

# Move horizontally to handover XY at safe lift height first (translation only)
goto_pose_arm0(np.array([arm0_handover_pos[0], arm0_handover_pos[1], lift_z]), q_arm0_handover)
# Lower vertically to the required handover height (0.15 < z < 0.20)
goto_pose_arm0(arm0_handover_pos, q_arm0_handover)

# 5. Move Arm1 to grasp the handle on the +X side:
# Target Arm1 gripper at x = 0.85 (0.04m from handle center toward tail).
# Buffer between grippers = 0.85 - 0.76 = 0.09m (9cm > 8cm buffer requirement).
arm1_handover_pos = np.array([0.85, 0.0, handover_z])

# Arm1 approaches horizontally at lift height first (translation only)
goto_pose_arm1(np.array([arm1_handover_pos[0], arm1_handover_pos[1], lift_z]), q_arm1_handover)
# Arm1 lowers down to grasp position
goto_pose_arm1(arm1_handover_pos, q_arm1_handover)

# Arm1 grasps the hammer handle
close_gripper_arm1()

# 6. Transfer completed: release Arm0 gripper
open_gripper_arm0()

# 7. Retract Arm0 to avoid collisions: vertical lift first, then retract back toward Arm0 base
goto_pose_arm0(np.array([arm0_handover_pos[0], arm0_handover_pos[1], lift_z]), q_arm0_handover)
goto_pose_arm0(np.array([0.55, 0.0, lift_z]), q_arm0_handover)