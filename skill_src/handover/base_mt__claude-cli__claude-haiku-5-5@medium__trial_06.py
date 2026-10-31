# Code block 0
Handover is planned at the midpoint x≈0.82 (between x=0.44 and x=1.18), with the hammer held at z=0.175 m. The hammer is yawed 90° during the transfer so the handle lies along X and Arm 1 can pinch it with its Y-opening gripper.

import numpy as np

# ---------------- Constants ----------------
Q_ARM0_OPEN_X = np.array([0.0, 0.707, 0.707, 0.0])   # Arm0 down, opening along X (pick)
Q_ARM0_OPEN_Y = np.array([0.0, 0.0, 1.0, 0.0])       # Arm0 down, opening along Y (= X-quat yawed 90 deg)
Q_ARM1_OPEN_Y = np.array([0.0, 0.0, 1.0, 0.0])       # Arm1 down, opening along Y (reference)

Z_TRANSFER = 0.175      # must lie in [0.15, 0.20] during handover
Z_CARRY = 0.25          # clearance height for carrying across the central gap
MID_X = 0.82            # midpoint between Arm0 (0.44) and Arm1 (1.18)
X_ARM0_HOLD = 0.78      # Arm0 holds the handle at this x
X_ARM1_GRASP = 0.86     # 8 cm center-to-center separation from Arm0 (>= 8 cm buffer)
X_ARM0_HOME = 0.30      # retreat position for Arm0 after release

# ---------------- 1. Perceive ----------------
hammer_pos, hammer_quat = get_hammer_pose()
pick_z = float(hammer_pos[2])   # handle-middle height from perception

# ---------------- 2. Arm0 picks handle middle ----------------
open_gripper_arm0()
goto_pose_arm0(np.array([hammer_pos[0], hammer_pos[1], pick_z]),
               Q_ARM0_OPEN_X, z_approach=0.10)   # approach from above
close_gripper_arm0()

# ---------------- 3. Lift straight up (stay over own side) ----------------
goto_pose_arm0(np.array([hammer_pos[0], hammer_pos[1], Z_CARRY]), Q_ARM0_OPEN_X)

# ---------------- 4. Carry toward midpoint in stages at safe height ----------------
# Intermediate waypoint keeps the hammer high while moving over the gap.
goto_pose_arm0(np.array([0.60, 0.0, Z_CARRY]), Q_ARM0_OPEN_X)
goto_pose_arm0(np.array([X_ARM0_HOLD, 0.0, Z_CARRY]), Q_ARM0_OPEN_X)

# ---------------- 5. Descend to transfer height ----------------
goto_pose_arm0(np.array([X_ARM0_HOLD, 0.0, Z_TRANSFER]), Q_ARM0_OPEN_X)

# ---------------- 6. Yaw hammer 90 deg in place so handle aligns with X ----------------
# Rotation only; translation is zero so the hammer stays at the transfer point.
goto_pose_arm0(np.array([X_ARM0_HOLD, 0.0, Z_TRANSFER]), Q_ARM0_OPEN_Y)

# ---------------- 7. Arm1 approaches handle from above, opening along Y ----------------
open_gripper_arm1()
# Pre-position Arm1 above the handle end, keeping >= 8 cm from Arm0's gripper.
goto_pose_arm1(np.array([X_ARM1_GRASP, 0.0, Z_TRANSFER]), Q_ARM1_OPEN_Y, z_approach=0.10)
close_gripper_arm1()

# ---------------- 8. Arm0 releases and retreats ----------------
open_gripper_arm0()
# Lift Arm0 vertically first so its fingers clear the handle without sweeping into Arm1.
goto_pose_arm0(np.array([X_ARM0_HOLD, 0.0, Z_CARRY]), Q_ARM0_OPEN_Y)
goto_pose_arm0(np.array([X_ARM0_HOME, 0.0, Z_CARRY]), Q_ARM0_OPEN_Y)

# ---------------- 9. Verify handover height ----------------
check_pos, _ = get_hammer_pose()
print("Hammer position after handover:", check_pos)

# Code block 1
import numpy as np

# ---------------- Constants ----------------
# Arm0 down, opening along X (reference: [0, 0.707, 0.707, 0])
Q_ARM0_OPEN_X = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 down, opening along Y (reference: [0, 1, 0, 0])
Q_ARM0_OPEN_Y = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 down, opening along Y (reference: [0, 0, 1, 0])
Q_ARM1_OPEN_Y = np.array([0.0, 0.0, 1.0, 0.0])

Z_TRANSFER = 0.175       # must lie in [0.15, 0.20] during handover
Z_CARRY = 0.25           # clearance height for carrying across the central gap
X_ARM0_HOLD = 0.78       # Arm0 holds handle middle here (near the midpoint of 0.44 and 1.18)
X_ARM1_GRASP = 0.88      # 10 cm separation from Arm0 gripper (>= 8 cm buffer)
X_ARM0_HOME = 0.30       # retreat position for Arm0 after release

# ---------------- 1. Perceive ----------------
hammer_pos, hammer_quat = get_hammer_pose()
pick_z = float(hammer_pos[2])

# ---------------- 2. Arm0 picks handle middle ----------------
open_gripper_arm0()
goto_pose_arm0(np.array([hammer_pos[0], hammer_pos[1], pick_z]),
               Q_ARM0_OPEN_X, z_approach=0.10)
close_gripper_arm0()

# ---------------- 3. Lift straight up over own side ----------------
goto_pose_arm0(np.array([hammer_pos[0], hammer_pos[1], Z_CARRY]), Q_ARM0_OPEN_X)

# ---------------- 4. Carry toward midpoint at safe height ----------------
goto_pose_arm0(np.array([0.60, 0.0, Z_CARRY]), Q_ARM0_OPEN_X)
goto_pose_arm0(np.array([X_ARM0_HOLD, 0.0, Z_CARRY]), Q_ARM0_OPEN_X)

# ---------------- 5. Descend to transfer height ----------------
goto_pose_arm0(np.array([X_ARM0_HOLD, 0.0, Z_TRANSFER]), Q_ARM0_OPEN_X)

# ---------------- 6. Yaw hammer 90 deg in place (rotation only) ----------------
goto_pose_arm0(np.array([X_ARM0_HOLD, 0.0, Z_TRANSFER]), Q_ARM0_OPEN_Y)

# ---------------- 7. Arm1 approaches handle end from above ----------------
open_gripper_arm1()
goto_pose_arm1(np.array([X_ARM1_GRASP, 0.0, Z_TRANSFER]), Q_ARM1_OPEN_Y, z_approach=0.10)
close_gripper_arm1()

# ---------------- 8. Arm0 releases and retreats vertically first ----------------
open_gripper_arm0()
goto_pose_arm0(np.array([X_ARM0_HOLD, 0.0, Z_CARRY]), Q_ARM0_OPEN_Y)
goto_pose_arm0(np.array([X_ARM0_HOME, 0.0, Z_CARRY]), Q_ARM0_OPEN_Y)

# ---------------- 9. Verify handover height ----------------
check_pos, _ = get_hammer_pose()
print("Hammer position after handover:", check_pos)