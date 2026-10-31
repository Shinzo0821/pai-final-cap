# Code block 0
import numpy as np

# Step 0: Ensure both grippers are opened initially
open_gripper_arm0()
open_gripper_arm1()

# Define reference quaternions (WXYZ)
# Arm0 facing down, opening along X-axis (to grasp handle aligned along Y-axis)
q_arm0_down_open_x = np.array([0.0, 0.70710678, 0.70710678, 0.0])
# Arm0 facing down, opening along Y-axis (after 90-deg Z-rotation, hammer aligns along X-axis)
q_arm0_down_open_y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down, opening along Y-axis (to grasp handle aligned along X-axis)
q_arm1_down_open_y = np.array([0.0, 0.0, 1.0, 0.0])

# Step 1: Detect hammer handle pose
hammer_pos, _ = get_hammer_pose()

# The hammer handle is aligned along Y with handle towards +Y and head towards -Y.
# We grasp slightly toward the head (-Y offset) so that ample handle length extends
# toward +Y for Arm 1 to grasp during handover.
arm0_grasp_pos = np.array([hammer_pos[0], hammer_pos[1] - 0.04, hammer_pos[2]])

# Approach hammer from above and close gripper
goto_pose_arm0(arm0_grasp_pos, q_arm0_down_open_x, z_approach=0.10)
close_gripper_arm0()

# Step 2: Lift hammer vertically to clear table surface safely
safe_lift_z = 0.25
goto_pose_arm0(np.array([arm0_grasp_pos[0], arm0_grasp_pos[1], safe_lift_z]), q_arm0_down_open_x)

# Step 3: Decompose movement: rotate in place so hammer aligns along X-axis
# This directs the handle toward Arm 1 (+X direction)
goto_pose_arm0(np.array([arm0_grasp_pos[0], arm0_grasp_pos[1], safe_lift_z]), q_arm0_down_open_y)

# Step 4: Move Arm 0 stepwise to the handover location near the midpoint
# Midpoint between x=0.44 and x=1.18 is x=0.81.
# Handover z must be between 0.15 and 0.20 (target z = 0.175).
handover_arm0_pos = np.array([0.73, 0.0, 0.175])

# Move horizontally at safe clearance height first
goto_pose_arm0(np.array([handover_arm0_pos[0], handover_arm0_pos[1], safe_lift_z]), q_arm0_down_open_y)
# Lower vertically to target handover height
goto_pose_arm0(handover_arm0_pos, q_arm0_down_open_y)

# Step 5: Move Arm 1 to grasp the handle extending towards +X
# Arm 1 grasps at x=0.84, maintaining an 11 cm buffer (> 8 cm requirement) from Arm 0
handover_arm1_pos = np.array([0.84, 0.0, 0.175])

# Arm 1 moves to safe pre-handover waypoint at high z
goto_pose_arm1(np.array([1.00, 0.0, safe_lift_z]), q_arm1_down_open_y)
# Arm 1 approaches handover grasp position from above
goto_pose_arm1(handover_arm1_pos, q_arm1_down_open_y, z_approach=0.08)

# Step 6: Complete the handover
# Arm 1 grasps the handle
close_gripper_arm1()

# Arm 0 releases the hammer
open_gripper_arm0()

# Step 7: Safely retract Arm 0 horizontally and then upward away from Arm 1
goto_pose_arm0(np.array([0.60, 0.0, 0.175]), q_arm0_down_open_y)
goto_pose_arm0(np.array([0.44, 0.0, safe_lift_z]), q_arm0_down_open_y)