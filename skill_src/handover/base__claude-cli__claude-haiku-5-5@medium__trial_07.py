# Code block 0
import numpy as np

# Reference quaternions (WXYZ)
Q0X = np.array([0.0, 0.70710678, 0.70710678, 0.0])  # Arm0 down, fingers along X (grips handle lying along Y)
Q0Y = np.array([0.0, 1.0, 0.0, 0.0])                # Arm0 down, fingers along Y (used after hammer is rotated so handle lies along X)
Q1Y = np.array([0.0, 0.0, 1.0, 0.0])                # Arm1 down, fingers along Y (grips handle lying along X)

# Safe transfer heights and waypoints
Z_LIFT = 0.25        # safe clearance height for travel
Z_HANDOVER = 0.175   # must stay within 0.15-0.20 during handover
X_HANDOVER0 = 0.72   # Arm0 grip x during handover (between arms, toward midpoint ~0.81)
X_RETREAT0 = 0.60    # Arm0 retreat x after release

# Read hammer pose (middle of handle)
hammer_pos, hammer_quat = get_hammer_pose()
mx, my, mz = hammer_pos

# Step 1: Arm0 grasps the handle, offset slightly toward the head side (-X after rotation).
# This leaves room for Arm1 to grasp the far handle tip with >= 8 cm gripper separation.
grasp0 = np.array([mx - 0.03, my, mz])

open_gripper_arm0()
# Approach from above, then close
goto_pose_arm0(grasp0, Q0X, z_approach=0.10)
close_gripper_arm0()

# Step 2: Lift straight up to a safe travel height
goto_pose_arm0(np.array([grasp0[0], my, Z_LIFT]), Q0X)

# Step 3: Translate horizontally toward the midpoint at safe height (still gripping along X)
goto_pose_arm0(np.array([X_HANDOVER0, my, Z_LIFT]), Q0X)

# Step 4: Rotate hammer 90 degrees about Z in place (-90 deg maps the head from -Y to -X, handle tip to +X).
# Grip point stays fixed, so the handle now lies along X and the head points toward Arm0.
goto_pose_arm0(np.array([X_HANDOVER0, my, Z_LIFT]), Q0Y)

# Step 5: Lower to handover height, keeping the hammer within the 0.15-0.20 m band
goto_pose_arm0(np.array([X_HANDOVER0, my, Z_HANDOVER]), Q0Y)

# Step 6: Arm1 approaches the handle tip (not the head) from the +X side.
# Target is 9 cm from Arm0's grip along X, which keeps the required >= 8 cm separation
# and stays on the handle because the tip lies at least 0.105 m from Arm0's grip.
grasp1 = np.array([X_HANDOVER0 + 0.09, my, Z_HANDOVER])

open_gripper_arm1()
goto_pose_arm1(grasp1, Q1Y, z_approach=0.10)
close_gripper_arm1()

# Step 7: Arm0 releases the hammer once Arm1 has a firm grip
open_gripper_arm0()

# Step 8: Arm0 retreats along -X at safe height to clear the hammer and Arm1
goto_pose_arm0(np.array([X_RETREAT0, my, Z_LIFT]), Q0Y)