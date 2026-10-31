# Code block 0
import numpy as np

# 1. Open both grippers
open_gripper_arm0()
open_gripper_arm1()

# 2. Get initial hammer handle pose
hammer_pos, _ = get_hammer_pose()

# Reference quaternions
q_arm0_open_x = np.array([0.0, 0.707, 0.707, 0.0])  # Gripper facing down, opening along X
q_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])      # Gripper facing down, opening along Y
q_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])      # Gripper facing down, opening along Y

# 3. Arm0 moves to grasp hammer handle closer to the head (-Y direction)
# The hammer lies along Y with handle towards +Y and head towards -Y.
# Grasping 4cm towards the head leaves sufficient handle space on +Y for Arm1.
grasp_pos = np.array([hammer_pos[0], hammer_pos[1] - 0.04, hammer_pos[2]])
goto_pose_arm0(grasp_pos, q_arm0_open_x, z_approach=0.10)
close_gripper_arm0()

# 4. Lift hammer vertically above table to clear obstacles
lift_pos = np.array([grasp_pos[0], grasp_pos[1], 0.20])
goto_pose_arm0(lift_pos, q_arm0_open_x)

# 5. Decompose motion: rotate Arm0 in place so the hammer handle aligns along X-axis
# Rotating to q_arm0_open_y directs the handle towards +X (Arm1) and head towards -X (Arm0)
goto_pose_arm0(lift_pos, q_arm0_open_y)

# 6. Stepwise translation to handover position near the midpoint (x ~ 0.81)
# With hammer center at x = 0.80, z = 0.175 (between 0.15 and 0.20),
# Arm0 holding offset (-0.04m) puts Arm0 gripper at x = 0.76.
handover_pos_arm0 = np.array([0.76, 0.0, 0.175])
goto_pose_arm0(np.array([handover_pos_arm0[0], handover_pos_arm0[1], 0.20]), q_arm0_open_y)
goto_pose_arm0(handover_pos_arm0, q_arm0_open_y)

# 7. Arm1 approaches the hammer handle at x = 0.85 (9cm buffer from Arm0 gripper)
# Approaching from above using z_approach ensures collision-free insertion
handover_pos_arm1 = np.array([0.85, 0.0, 0.175])
goto_pose_arm1(handover_pos_arm1, q_arm1_open_y, z_approach=0.10)

# 8. Arm1 grasps the hammer handle
close_gripper_arm1()

# 9. Arm0 releases hammer and retracts to maintain clearance
open_gripper_arm0()
goto_pose_arm0(np.array([0.60, 0.0, 0.25]), q_arm0_open_y)