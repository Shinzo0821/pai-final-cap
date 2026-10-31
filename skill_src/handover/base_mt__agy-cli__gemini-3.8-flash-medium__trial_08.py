# Code block 0
import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get hammer pose (middle of the handle)
hammer_pos, _ = get_hammer_pose()

# Reference quaternions
q_arm0_down_x = np.array([0.0, 0.707, 0.707, 0.0])
q_arm0_down_y = np.array([0.0, 1.0, 0.0, 0.0])
q_arm1_down_y = np.array([0.0, 0.0, 1.0, 0.0])

# Grasp hammer near the head side of the handle (-Y direction)
# Handle length is 0.15m to 0.25m, so -0.05m along Y is safely on the handle towards the head
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] - 0.05, hammer_pos[2]])

# Arm 0 approaches and grasps the hammer
goto_pose_arm0(grasp_pos_arm0, q_arm0_down_x, z_approach=0.10)
close_gripper_arm0()

# Lift hammer vertically to handover height (z = 0.175 is within [0.15, 0.20])
handover_z = 0.175
lift_pos_arm0 = np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], handover_z])
goto_pose_arm0(lift_pos_arm0, q_arm0_down_x)

# Rotate hammer 90 degrees so it aligns along the X-axis (handle points towards +X / Arm 1)
goto_pose_arm0(lift_pos_arm0, q_arm0_down_y)

# Translate Arm 0 to handover waypoint near midpoint (x = 0.75, y = 0.0, z = 0.175)
handover_pos_arm0 = np.array([0.75, 0.0, handover_z])
goto_pose_arm0(handover_pos_arm0, q_arm0_down_y)

# Decompose Arm 1 motion stepwise into rotation, XY translation, and Z approach
# Align orientation high above first
goto_pose_arm1(np.array([1.18, 0.0, 0.28]), q_arm1_down_y)

# Translate Arm 1 in XY to above the handover grasp point (x = 0.85 provides 10cm buffer > 8cm buffer)
handover_pos_arm1 = np.array([0.85, 0.0, handover_z])
goto_pose_arm1(np.array([0.85, 0.0, 0.28]), q_arm1_down_y)

# Move Arm 1 vertically down to grasp the hammer handle
goto_pose_arm1(handover_pos_arm1, q_arm1_down_y)

# Arm 1 grasps the hammer handle
close_gripper_arm1()

# Handover transfer: Arm 0 releases after Arm 1 has safely gripped
open_gripper_arm0()

# Safely retract Arm 0 away from Arm 1
goto_pose_arm0(np.array([0.65, 0.0, handover_z]), q_arm0_down_y)
goto_pose_arm0(np.array([0.50, 0.0, 0.25]), q_arm0_down_y)