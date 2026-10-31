# Code block 0
# Handover plan: Arm 0 grasps the handle off-center, rotates the hammer 90° about Z, and hands the handle end to Arm 1 at z = 0.18.
import numpy as np

# Reference quaternions (WXYZ)
Q0_X = np.array([0.0, 0.707, 0.707, 0.0])  # Arm0 facing down, jaws along X (straddle handle sides; handle is along Y)
Q0_Y = np.array([0.0, 1.0, 0.0, 0.0])      # Arm0 facing down, jaws along Y (= Q0_X yawed by -90 deg, so handle lies along X)
Q1_Y = np.array([0.0, 0.0, 1.0, 0.0])      # Arm1 facing down, jaws along Y (handle lies along X, jaws straddle sides)

HANDOVER_Z = 0.18          # target hammer z during handover (must be within 0.15-0.20)
LIFT_Z = 0.18              # lift height for transit, keeps the head clear of the table

# Step 0: make sure both grippers start open
open_gripper_arm0()
open_gripper_arm1()

# Step 1: read the hammer pose (middle of the handle, handle along Y, head toward -Y)
p, _ = get_hammer_pose()
p = np.asarray(p, dtype=float)

# Grasp the handle 5 cm toward the head from its middle.
# Handle half-length is at least 0.075 m, so this point is always on the handle.
# After the -90 deg yaw, this leaves about 0.12 m of handle free toward +X for Arm 1.
Pg = np.array([p[0], p[1] - 0.05, p[2]])

# Step 2: Arm0 approaches from above, grasps the handle, and lifts
goto_pose_arm0(Pg, Q0_X, z_approach=0.08)
close_gripper_arm0()

goto_pose_arm0(np.array([Pg[0], Pg[1], LIFT_Z]), Q0_X)

# Step 3: move toward the midpoint (x = 0.81) while yawing -90 deg about Z.
# Yawing -90 deg maps the handle's +Y end to +X, so the free handle end points at Arm1.
# Hold point H sits slightly on Arm0's side of the midpoint.
H = np.array([0.68, 0.0, HANDOVER_Z])
goto_pose_arm0(H, Q0_Y)

# Step 4: Arm1 grasps the free handle end, 0.12 m from Arm0's grip point toward +X.
# The grip point is at x = 0.80, so the two grippers are 12 cm apart (above the 8 cm minimum).
G = H + np.array([0.12, 0.0, 0.0])
open_gripper_arm1()
goto_pose_arm1(G, Q1_Y, z_approach=0.08)
close_gripper_arm1()

# Step 5: Arm0 releases, then retracts straight up with the gripper open
open_gripper_arm0()
goto_pose_arm0(H + np.array([0.0, 0.0, 0.10]), Q0_Y)

# Step 6: report the final hammer pose for verification
p_final, _ = get_hammer_pose()
print("Hammer position after handover:", p_final)