# Code block 0
import numpy as np

# 1. Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# 2. Get the hammer pose (returns pose of the middle of the handle)
# Hammer initially lies flat on table along Y-axis: handle toward +Y, head toward -Y.
hammer_pos, _ = get_hammer_pose()

# Reference quaternions
q_arm0_open_x = np.array([0.0, 0.707, 0.707, 0.0])  # Facing down, opening along X
q_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])      # Facing down, opening along Y
q_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])      # Facing down, opening along Y

# 3. Grasp the hammer with Arm 0
# Offset grasp toward the hammer head (-Y) by 4cm so the handle (+Y) remains free for Arm 1.
# Min handle length is 15cm (half-length 7.5cm), so 4cm is safely on the handle.
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] - 0.04, hammer_pos[2]])
goto_pose_arm0(grasp_pos_arm0, q_arm0_open_x, z_approach=0.10)
close_gripper_arm0()

# 4. Lift the hammer vertically to handover height (z in [0.15, 0.20])
handover_z = 0.175
lift_pos = np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], handover_z])
goto_pose_arm0(lift_pos, q_arm0_open_x)

# 5. Rotate Arm 0 in place to align hammer along X-axis
# Rotating from opening along X to opening along Y rotates the grasped hammer by 90 degrees,
# orienting the handle toward +X (directly facing Arm 1).
goto_pose_arm0(lift_pos, q_arm0_open_y)

# 6. Translate Arm 0 stepwise to the handover position near the midpoint of arms (x ~ 0.81)
handover_pos_arm0 = np.array([0.765, 0.0, handover_z])
mid_pos_arm0 = (lift_pos + handover_pos_arm0) / 2.0
goto_pose_arm0(mid_pos_arm0, q_arm0_open_y)
goto_pose_arm0(handover_pos_arm0, q_arm0_open_y)

# 7. Move Arm 1 to grasp the exposed hammer handle
# Arm 1 is placed at x = 0.855 (9cm buffer > 8cm required minimum buffer from Arm 0 at x = 0.765).
# Approaching from above (z_approach) ensures collision-free insertion.
handover_pos_arm1 = np.array([0.855, 0.0, handover_z])
goto_pose_arm1(handover_pos_arm1, q_arm1_open_y, z_approach=0.10)

# 8. Grasp with Arm 1 and release Arm 0 to complete handover
close_gripper_arm1()
open_gripper_arm0()