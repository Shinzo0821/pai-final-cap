# Code block 0
import numpy as np

# Strategy:
# 1. Arm0 grasps the handle near the head end (~5 cm from the handle midpoint toward -Y),
#    with the gripper opening along X because the handle lies along Y.
# 2. Arm0 lifts the hammer, moves it to the handover area and rotates the gripper 90 deg about Z.
#    Rotating from [0,.707,.707,0] to [0,1,0,0] maps +Y to +X, so the handle then points toward Arm1.
# 3. Arm0 lowers the hammer so its z is about 0.175, then corrects z using the measured hammer pose.
# 4. Arm1 grasps the free end of the handle about 10 cm in +X from Arm0's gripper.
#    The gripper opens along Y, the approach is from above, and the grippers stay more than 8 cm apart.
# 5. Arm1 closes, Arm0 opens and retracts upward and toward -X.

q0_open_x = np.array([0.0, 0.707, 0.707, 0.0])      # arm0 down, opening along X
q0_open_y = np.array([0.0, 1.0, 0.0, 0.0])          # arm0 down, opening along Y
q0_mid = np.array([0.0, 0.924, 0.383, 0.0])         # halfway rotation (45 deg)
q1_open_y = np.array([0.0, 0.0, 1.0, 0.0])          # arm1 down, opening along Y

target_hz = 0.175
mid_x = 0.81
grip_offset = 0.05  # distance of arm0 grasp from the handle midpoint (toward the head)

open_gripper_arm0()
open_gripper_arm1()

# ---- Arm0 grasps the handle near the head side ----
p, _ = get_hammer_pose()
p = np.array(p, dtype=float)
grasp0 = np.array([p[0], p[1] - grip_offset, p[2]])
goto_pose_arm0(grasp0, q0_open_x, z_approach=0.12)
close_gripper_arm0()

# ---- Lift straight up ----
lift_z = max(p[2] + 0.18, 0.30)
goto_pose_arm0(np.array([grasp0[0], grasp0[1], lift_z]), q0_open_x)

# ---- Translate toward the handover area (arm0 side of the midpoint) at the lifted height ----
arm0_hand_x = mid_x - grip_offset   # ~0.76; the handle midpoint ends near x = 0.81
mid_pos = np.array([(grasp0[0] + arm0_hand_x) / 2.0, grasp0[1] / 2.0, lift_z])
goto_pose_arm0(mid_pos, q0_open_x)
hand_pos_high = np.array([arm0_hand_x, 0.0, lift_z])
goto_pose_arm0(hand_pos_high, q0_open_x)

# ---- Rotate stepwise in place so the handle points toward +X (toward arm1) ----
goto_pose_arm0(hand_pos_high, q0_mid)
goto_pose_arm0(hand_pos_high, q0_open_y)

# ---- Lower to the handover height, then correct using the measured hammer z ----
gripper_z = target_hz
goto_pose_arm0(np.array([arm0_hand_x, 0.0, (lift_z + gripper_z) / 2.0]), q0_open_y)
goto_pose_arm0(np.array([arm0_hand_x, 0.0, gripper_z]), q0_open_y)
hp, _ = get_hammer_pose()
hp = np.array(hp, dtype=float)
dz = target_hz - hp[2]
if abs(dz) > 0.005:
    gripper_z = gripper_z + dz
    goto_pose_arm0(np.array([arm0_hand_x, 0.0, gripper_z]), q0_open_y)
    hp, _ = get_hammer_pose()
    hp = np.array(hp, dtype=float)

# ---- Arm1 grasps the handle on the +X side of the midpoint (away from arm0 and the head) ----
arm1_x = max(hp[0] + 0.05, arm0_hand_x + 0.10)   # keep at least ~10 cm between grippers
grasp1 = np.array([arm1_x, hp[1], hp[2]])
# Pre-position above on the arm1 side first, then descend vertically
goto_pose_arm1(np.array([arm1_x + 0.05, hp[1], hp[2] + 0.20]), q1_open_y)
goto_pose_arm1(grasp1, q1_open_y, z_approach=0.12)
close_gripper_arm1()

# ---- Arm0 releases and retracts safely (up, then back toward -X) ----
open_gripper_arm0()
goto_pose_arm0(np.array([arm0_hand_x, 0.0, gripper_z + 0.12]), q0_open_y)
goto_pose_arm0(np.array([0.50, 0.0, gripper_z + 0.15]), q0_open_y)

# ---- Arm1 holds the hammer at the handover height ----
hp2, _ = get_hammer_pose()
hp2 = np.array(hp2, dtype=float)
dz2 = target_hz - hp2[2]
if abs(dz2) > 0.01:
    goto_pose_arm1(np.array([grasp1[0], grasp1[1], grasp1[2] + dz2]), q1_open_y)

# Code block 1
import numpy as np

# The previous run produced no output, so the result cannot be verified yet.
# The main risk is the 90 deg rotation of arm0. If it sent the handle toward -X (arm0)
# instead of +X, arm1 would have closed on the head or on empty space,
# and the hammer could have dropped once arm0 released it.
# This step only reads the state and does not move any arm.
hp, hq = get_hammer_pose()
hp = np.array(hp, dtype=float)
print("hammer handle-mid position:", hp)
print("hammer quaternion (may be unreliable):", np.array(hq, dtype=float))
print("hammer z in [0.15, 0.20]:", 0.15 <= hp[2] <= 0.20)
print("hammer appears held above table (z > 0.10):", hp[2] > 0.10)