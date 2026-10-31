# Code block 0
import numpy as np

# Define reference quaternions as specified
# Arm0 facing down opening along X-axis (to grasp hammer lying along Y-axis)
q_arm0_open_x = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down opening along Y-axis (rotates hammer 90 deg to align with X-axis)
q_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down opening along Y-axis (to grasp hammer aligned with X-axis)
q_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Initialize both grippers to open state
open_gripper_arm0()
open_gripper_arm1()

# 1. Perception: get initial pose of hammer handle center
hammer_pos, _ = get_hammer_pose()

# 2. Compute grasp position for Arm 0
# Hammer handle length is 0.15m - 0.25m, aligned along Y with head at -Y and handle towards +Y.
# Grasp 0.05m towards the head (-Y) on the handle to leave room for Arm 1 to grasp the handle.
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] - 0.05, hammer_pos[2]])

# 3. Approach hammer from above and grasp
goto_pose_arm0(grasp_pos_arm0, q_arm0_open_x, z_approach=0.1)
close_gripper_arm0()

# 4. Vertical lift (pure translation to avoid collisions with table)
# Target z = 0.175m (must be strictly within [0.15, 0.20] for handover success)
z_handover = 0.175
lift_pos_arm0 = np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], z_handover])
goto_pose_arm0(lift_pos_arm0, q_arm0_open_x)

# 5. Rotate hammer 90 degrees in-place (pure rotation)
# Rotating from q_arm0_open_x to q_arm0_open_y aligns the hammer along the X-axis,
# pointing the handle tip towards Arm 1 (+X) and the head towards Arm 0 (-X).
goto_pose_arm0(lift_pos_arm0, q_arm0_open_y)

# 6. Translate stepwise to the handover location
# Arm0 starting x ~ 0.44, Arm1 starting x ~ 1.18; midpoint is x ~ 0.81.
# Since Arm0 holds the handle 0.05m behind center, placing Arm0 at x = 0.76 centers the handle at x = 0.81.
mid_trans_pos = np.array([(lift_pos_arm0[0] + 0.76) / 2.0, lift_pos_arm0[1] / 2.0, z_handover])
goto_pose_arm0(mid_trans_pos, q_arm0_open_y)

handover_pos_arm0 = np.array([0.76, 0.0, z_handover])
goto_pose_arm0(handover_pos_arm0, q_arm0_open_y)

# 7. Arm 1 approaches handover pose from above
# Arm 1 targets x = 0.86, grasping the handle 0.05m ahead of center.
# Distance between grippers is 0.86 - 0.76 = 0.10m (10cm), satisfying the 8cm safety buffer.
handover_pos_arm1 = np.array([0.86, 0.0, z_handover])
goto_pose_arm1(handover_pos_arm1, q_arm1_open_y, z_approach=0.1)

# 8. Complete handover
# Secure grip with Arm 1 first before releasing Arm 0 to prevent dropping into the central gap
close_gripper_arm1()
open_gripper_arm0()

# 9. Retract Arm 0 safely away from the handover point
retract_pos_arm0 = np.array([0.60, 0.0, z_handover])
goto_pose_arm0(retract_pos_arm0, q_arm0_open_y)