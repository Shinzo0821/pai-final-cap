# Code block 0
# Plan: Arm 0 grasps mid-handle, yaws the hammer so the handle lies along X,
# transfers it at the midpoint (x≈0.81) with hammer z=0.175, and Arm 1 grasps the handle.
import numpy as np

def _unit(q):
    q = np.asarray(q, dtype=float)
    return q / np.linalg.norm(q)

# Quaternions (WXYZ)
Q_X_OPEN = _unit([0.0, 0.707, 0.707, 0.0])   # Arm0 down, jaws along X (pinch handle width while handle is along Y)
Q_Y_OPEN_ARM0 = _unit([0.0, 1.0, 0.0, 0.0])  # Arm0 down, jaws along Y (after -90 deg yaw of hammer, handle along X)
Q_Y_OPEN_ARM1 = _unit([0.0, 0.0, 1.0, 0.0])  # Arm1 down, jaws along Y (pinches handle width when handle is along X)

HANDOVER_Z = 0.175     # required hammer z during handover (0.15-0.20)
TRANSIT_Z = 0.30       # safe height for horizontal travel, well above hammer and grippers
LIFT = 0.12            # vertical clearance used for lifting and yaw

# Read hammer pose (middle of handle)
hammer_pos, _ = get_hammer_pose()
mid = np.asarray(hammer_pos, dtype=float)

# Grasp point: 4 cm from handle middle toward -Y.
# Rationale: after a -90 deg yaw about this point, the handle extends toward +X (toward Arm 1)
# by at least 0.115 m, and the head ends up on the -X side (toward Arm 0), so Arm 1 can grasp the handle.
G = mid + np.array([0.0, -0.04, 0.0])

# Target handover point at the midpoint between the arms (x = (0.44 + 1.18) / 2 ≈ 0.81, shifted for the offset).
# Arm 0 holds G at x = 0.765; Arm 1 grasps the handle 0.10 m further along +X, at x = 0.865.
HANDOVER_G = np.array([0.765, 0.0, HANDOVER_Z])
ARM1_GRASP = HANDOVER_G + np.array([0.10, 0.0, 0.0])

# ---- Step 1: Arm 0 grasps the handle ----
open_gripper_arm0()
goto_pose_arm0(G, Q_X_OPEN, z_approach=0.10)   # approach from above
close_gripper_arm0()

# ---- Step 2: Lift straight up (translation only) ----
goto_pose_arm0(G + np.array([0.0, 0.0, LIFT]), Q_X_OPEN)

# ---- Step 3: Yaw the gripper -90 deg about G at constant height (rotation only) ----
# The hammer rotates with the gripper about the vertical axis through G, so the handle ends up along +X.
goto_pose_arm0(G + np.array([0.0, 0.0, LIFT]), Q_Y_OPEN_ARM0)

# ---- Step 4: Translate horizontally at transit height to above the handover point ----
goto_pose_arm0(np.array([HANDOVER_G[0], HANDOVER_G[1], TRANSIT_Z]), Q_Y_OPEN_ARM0)

# ---- Step 5: Descend to handover height (z = 0.175) ----
goto_pose_arm0(HANDOVER_G, Q_Y_OPEN_ARM0)

# ---- Step 6: Arm 1 approaches the handle from above and grasps it ----
# Jaws along Y pinch across the handle width (handle now lies along X).
open_gripper_arm1()
goto_pose_arm1(ARM1_GRASP, Q_Y_OPEN_ARM1, z_approach=0.10)
close_gripper_arm1()

# ---- Step 7: Check hammer height while Arm 0 is still holding it ----
check_pos, _ = get_hammer_pose()
print("Hammer z after Arm 1 grasp:", float(check_pos[2]))

# ---- Step 8: Arm 0 releases only after Arm 1 has closed on the handle ----
open_gripper_arm0()

# ---- Step 9: Retract Arm 0 vertically, then move away along -X (away from Arm 1) ----
goto_pose_arm0(np.array([HANDOVER_G[0], HANDOVER_G[1], TRANSIT_Z]), Q_Y_OPEN_ARM0)
goto_pose_arm0(np.array([0.60, 0.0, TRANSIT_Z]), Q_Y_OPEN_ARM0)