# Code block 0
import numpy as np

# ---------------- Strategy ----------------
# The hammer lies along Y, with the handle toward +Y and the head toward -Y.
# get_hammer_pose() returns the middle of the handle.
# 1) Arm0 grasps the handle close to the head (middle - 0.05 m). The gripper
#    opens along X, perpendicular to the handle. This leaves the free handle end for Arm1.
# 2) Arm0 lifts the hammer high, then translates toward the handover zone.
# 3) Arm0 rotates the gripper by -90 deg about Z in steps. The handle then points +X, toward Arm1.
#    The quaternion for opening along X is [0, .707, .707, 0] = Rz(+90) * [0, 1, 0, 0].
#    So rotating to [0, 1, 0, 0] maps the handle from +Y to +X.
# 4) Arm0 lowers so the handle z is about 0.175, inside the required 0.15-0.20 range.
#    The handover happens near the midpoint x of about 0.81.
# 5) Arm1 (opening along Y, perpendicular to the handle) approaches from above.
#    It grasps the handle about 0.105 m beyond Arm0's grasp point.
#    The handle end is at least 0.125 m beyond it, and the gripper gap stays above 8 cm.
# 6) Arm1 closes, Arm0 opens and retreats up and back.

hammer_pos, _ = get_hammer_pose()
hammer_pos = np.array(hammer_pos, dtype=float)

q0_open_x = np.array([0.0, 0.70710678, 0.70710678, 0.0])   # Arm0 down, open along X
q0_mid = np.array([0.0, 0.92387953, 0.38268343, 0.0])      # Arm0 down, intermediate 45 deg
q0_open_y = np.array([0.0, 1.0, 0.0, 0.0])                 # Arm0 down, open along Y
q1_open_y = np.array([0.0, 0.0, 1.0, 0.0])                 # Arm1 down, open along Y

# ---------------- Arm0 grasp ----------------
open_gripper_arm0()
open_gripper_arm1()

grasp_offset = 0.05
grasp0 = hammer_pos + np.array([0.0, -grasp_offset, 0.0])

# Go above the grasp point first, then descend with the approach motion
goto_pose_arm0(grasp0 + np.array([0.0, 0.0, 0.15]), q0_open_x)
goto_pose_arm0(grasp0, q0_open_x, z_approach=0.10)
close_gripper_arm0()

# ---------------- Lift ----------------
lift_z = max(grasp0[2] + 0.20, 0.32)
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), q0_open_x)

# ---------------- Move toward handover zone (translation only) ----------------
mid_x = 0.81
handover_z = 0.175
sep = 0.105                           # distance between the two grasp points along the handle
arm0_hx = mid_x - sep / 2.0           # about 0.7575
arm1_hx = arm0_hx + sep               # about 0.8625
handover_y = 0.0

# Move in steps: first along Y to the centerline, then along X
goto_pose_arm0(np.array([grasp0[0], handover_y, lift_z]), q0_open_x)
goto_pose_arm0(np.array([arm0_hx, handover_y, lift_z]), q0_open_x)

# ---------------- Rotate (rotation only, stepwise) ----------------
goto_pose_arm0(np.array([arm0_hx, handover_y, lift_z]), q0_mid)
goto_pose_arm0(np.array([arm0_hx, handover_y, lift_z]), q0_open_y)

# ---------------- Lower to handover height ----------------
goto_pose_arm0(np.array([arm0_hx, handover_y, (lift_z + handover_z) / 2.0]), q0_open_y)
goto_pose_arm0(np.array([arm0_hx, handover_y, handover_z]), q0_open_y)

# Re-read the hammer pose to refine Arm1's grasp location
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)
# The handle middle should be about grasp_offset beyond Arm0 along +X.
# Arm1 grasps at Arm0 x + sep. Use the measured y/z if they are sensible.
arm1_y = hp[1] if abs(hp[1] - handover_y) < 0.05 else handover_y
arm1_z = hp[2] if 0.12 < hp[2] < 0.23 else handover_z
arm1_grasp = np.array([arm1_hx, arm1_y, arm1_z])

# ---------------- Arm1 approach and grasp ----------------
open_gripper_arm1()
# Move Arm1 high above its grasp point (translation in steps)
goto_pose_arm1(np.array([1.05, arm1_y, arm1_z + 0.20]), q1_open_y)
goto_pose_arm1(np.array([arm1_hx, arm1_y, arm1_z + 0.20]), q1_open_y)
# Descend straight down onto the handle end
goto_pose_arm1(arm1_grasp, q1_open_y, z_approach=0.10)
close_gripper_arm1()

# ---------------- Release Arm0 and retreat ----------------
open_gripper_arm0()
goto_pose_arm0(np.array([arm0_hx, handover_y, handover_z + 0.12]), q0_open_y)
goto_pose_arm0(np.array([0.50, handover_y, handover_z + 0.12]), q0_open_y)

# Arm1 keeps holding the hammer, with the handle z staying within 0.15-0.20
goto_pose_arm1(arm1_grasp, q1_open_y)