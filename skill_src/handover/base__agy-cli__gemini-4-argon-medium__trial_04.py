# Code block 0
import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get initial hammer pose (position of the middle of the hammer handle)
hammer_pos, _ = get_hammer_pose()

# Reference quaternions
# Arm0 facing down, opening along X-axis (good for grasping handle aligned along Y-axis)
quat_arm0_open_x = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down, opening along Y-axis (rotates hammer 90 deg so handle aligns along X-axis)
quat_arm0_open_y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, opening along Y-axis (good for grasping handle aligned along X-axis)
quat_arm1_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Step 1: Arm 0 grasps the hammer near the hammer head (-Y direction from handle center)
# Since handle length is between 0.15m and 0.25m, an offset of -0.05m in Y from the handle center
# safely grasps the handle near the head, leaving the +Y end of the handle free for Arm 1.
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] - 0.05, hammer_pos[2]])
goto_pose_arm0(grasp_pos_arm0, quat_arm0_open_x, z_approach=0.1)
close_gripper_arm0()

# Step 2: Lift the hammer up to handover height (z between 0.15 and 0.20 -> use 0.18)
handover_z = 0.18
lift_pos_arm0 = np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], handover_z])
goto_pose_arm0(lift_pos_arm0, quat_arm0_open_x)

# Step 3: Rotate the hammer in place so the free handle end points toward Arm 1 (+X direction).
# Moving from [0, 0.707, 0.707, 0] to [0, 1, 0, 0] is a +90 deg rotation around Z.
# A +90 deg rotation around Z maps the +Y handle vector to -X, whereas -90 deg maps +Y to +X.
# Wait: let's check both or see which way [0, 1, 0, 0] rotates from [0, 0.707, 0.707, 0]:
# q_start = [0, 1/sqrt(2), 1/sqrt(2), 0]
# q_end = [0, 1, 0, 0] (which is equivalent to [0, -1, 0, 0])
# Wait: instead of rotating the hammer to X-axis (where +90 vs -90 deg rotation could point the head or handle to +X),
# can we keep the hammer aligned along the Y-axis during handover, or rotate it?
# Let's check Arm 1's reference quaternion:
# Only ONE reference quaternion is provided for Arm 1:
# "Arm1 gripper facing down opening along Y-axis: [0, 0, 1, 0]."
# Because Arm 1's gripper opens along the Y-axis, the hammer handle MUST be aligned along the X-axis
# so that Arm 1's fingers (moving along Y) can close around the handle (extending along X) without hitting it!
# Let's verify the rotation from quat_arm0_open_x to quat_arm0_open_y:
# For q = [0, x, y, 0]:
# A vector v in gripper frame rotated by q = [0, cos(theta), sin(theta), 0]:
# R(q) = [[cos(2*theta), sin(2*theta), 0], [sin(2*theta), -cos(2*theta), 0], [0, 0, -1]]
# For q_start = [0, cos(pi/4), sin(pi/4), 0] = [0, 0.707, 0.707, 0] (2*theta = pi/2):
# R(q_start) = [[0, 1, 0], [1, 0, 0], [0, 0, -1]].
# At grasp, the free handle end is in world +Y direction from Arm 0's gripper: v_world = [0, +1, 0].
# In gripper frame, v_gripper = R(q_start)^T @ v_world = [1, 0, 0].
# Now when Arm 0 moves to q_end = [0, 1, 0, 0] (where 2*theta = 0):
# R(q_end) = [[1, 0, 0], [0, -1, 0], [0, 0, -1]].
# Then in world frame, the free handle end becomes:
# v_world_new = R(q_end) @ v_gripper = R(q_end) @ [1, 0, 0] = [1, 0, 0] (+X direction!).
# That's why the prompt specifically gave [0, 1, 0, 0] for Arm 0! It points the free handle directly toward +X (Arm 1)!

# Rotate Arm 0 in place at lift_pos_arm0 so handle points toward +X
goto_pose_arm0(lift_pos_arm0, quat_arm0_open_y)

# Step 4: Translate Arm 0 to the handover position near the midpoint of the initial gripper positions.
# Midpoint of x=0.44 and x=1.18 is x=0.81, y=0.0.
# Since Arm 0 holds the hammer at 0.05m from the handle center, and the free handle extends toward +X,
# let's place Arm 0 at x = 0.75, y = 0.0, z = 0.18 so the hammer midpoint is at x = 0.80,
# and Arm 1 can grasp at x = 0.85 (giving a 10cm buffer between grippers, > 8cm minimum!).
handover_pos_arm0 = np.array([0.75, 0.0, handover_z])
goto_pose_arm0(handover_pos_arm0, quat_arm0_open_y)

# Re-read hammer pose at handover to get exact handle center position and height
hammer_pos_ho, _ = get_hammer_pose()

# Step 5: Move Arm 1 to grasp the handle on the +X side, keeping at least 9-10cm away from Arm 0 (x=0.75)
# Handle center is around x = 0.80 (hammer_pos_ho[0]).
# Grasping at x = 0.85 is 0.05m from handle center (well within even the shortest 0.15m handle, which extends 0.075m from center)
# and 0.10m (10cm) from Arm 0's gripper at x = 0.75.
grasp_x_arm1 = max(hammer_pos_ho[0] + 0.04, 0.84)
handover_pos_arm1 = np.array([grasp_x_arm1, hammer_pos_ho[1], hammer_pos_ho[2]])

# Approach from above using z_approach to avoid any horizontal collision with the handle
goto_pose_arm1(handover_pos_arm1, quat_arm1_open_y, z_approach=0.1)

# Close Arm 1 gripper to grasp the handle
close_gripper_arm1()

# Step 6: Release Arm 0 gripper and retract Arm 0 safely away from the hammer
open_gripper_arm0()

# Lift Arm 0 straight up first to clear the hammer before translating back
retract_up_arm0 = np.array([handover_pos_arm0[0], handover_pos_arm0[1], handover_z + 0.12])
goto_pose_arm0(retract_up_arm0, quat_arm0_open_y)

# Move Arm 0 back toward its starting region
retract_back_arm0 = np.array([0.45, 0.0, handover_z + 0.12])
goto_pose_arm0(retract_back_arm0, quat_arm0_open_y)