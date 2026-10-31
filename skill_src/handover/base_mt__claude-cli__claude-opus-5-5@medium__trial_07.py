# Code block 0
import numpy as np

# ---------------- Strategy ----------------
# Arm 0 grasps the handle near the head end. It lifts the hammer and yaws it by -90 deg so the handle
# points along +X toward Arm 1, with the head toward Arm 0. The hammer is presented near the midpoint
# between the arms at z ~0.175. Arm 1 then grasps the free handle end from above. The two grippers are
# about 0.10 m apart along X, which is more than the 8 cm buffer.

Q0_OPEN_X = np.array([0.0, 0.70710678, 0.70710678, 0.0])   # arm0 down, opening along X (handle along Y)
Q0_MID = np.array([0.0, 0.92387953, 0.38268343, 0.0])      # intermediate yaw (45 deg)
Q0_OPEN_Y = np.array([0.0, 1.0, 0.0, 0.0])                 # arm0 down, opening along Y (handle along X)
Q1_OPEN_Y = np.array([0.0, 0.0, 1.0, 0.0])                 # arm1 down, opening along Y

D = 0.05            # grasp offset from handle middle (arm0 toward head, arm1 toward handle end)
HANDOVER_X = 0.81   # midpoint of initial gripper x positions
HANDOVER_Y = 0.0
HANDOVER_Z = 0.175  # desired hammer z during handover
SAFE_Z_LIFT = 0.30

open_gripper_arm0()
open_gripper_arm1()

# ---------------- Arm 0 grasp ----------------
pos, _ = get_hammer_pose()
pos = np.array(pos, dtype=float)
table_z = pos[2]

grasp0 = np.array([pos[0], pos[1] - D, pos[2]])
# Hover above first, then descend straight down
goto_pose_arm0(grasp0 + np.array([0, 0, 0.12]), Q0_OPEN_X)
goto_pose_arm0(grasp0, Q0_OPEN_X, z_approach=0.10)
close_gripper_arm0()

# ---------------- Lift (pure translation) ----------------
lift0 = np.array([grasp0[0], grasp0[1], max(SAFE_Z_LIFT, table_z + 0.18)])
goto_pose_arm0(grasp0 + np.array([0, 0, 0.05]), Q0_OPEN_X)
goto_pose_arm0(lift0, Q0_OPEN_X)

# Measure the offset between the hammer and the commanded gripper position
h, _ = get_hammer_pose()
h = np.array(h, dtype=float)
z_off = h[2] - lift0[2]

# ---------------- Rotate in place (pure rotation, stepwise) ----------------
goto_pose_arm0(lift0, Q0_MID)
goto_pose_arm0(lift0, Q0_OPEN_Y)

# ---------------- Translate to handover location ----------------
# Arm0 gripper sits at HANDOVER_X - D so that the handle middle is near the midpoint
target0_high = np.array([HANDOVER_X - D, HANDOVER_Y, lift0[2]])
goto_pose_arm0(np.array([(lift0[0] + target0_high[0]) / 2, (lift0[1] + HANDOVER_Y) / 2, lift0[2]]), Q0_OPEN_Y)
goto_pose_arm0(target0_high, Q0_OPEN_Y)
target0 = np.array([HANDOVER_X - D, HANDOVER_Y, HANDOVER_Z - z_off])
goto_pose_arm0(target0, Q0_OPEN_Y)

# Correct the hammer height if needed so it is inside the [0.15, 0.20] window
h, _ = get_hammer_pose()
h = np.array(h, dtype=float)
if h[2] < 0.155 or h[2] > 0.195:
    target0 = target0 + np.array([0, 0, HANDOVER_Z - h[2]])
    goto_pose_arm0(target0, Q0_OPEN_Y)
    h, _ = get_hammer_pose()
    h = np.array(h, dtype=float)

# ---------------- Arm 1 grasp of the handle end ----------------
# The handle runs along +X from the arm0 gripper; the handle middle is at h. Arm1 grasps at h + D along X.
grasp1 = np.array([h[0] + D, h[1], h[2]])
# Keep the arm1 gripper at least 8 cm from the arm0 gripper
grasp1[0] = max(grasp1[0], target0[0] + 0.09)

# Approach from Arm 1's side at a safe height, then descend vertically
goto_pose_arm1(np.array([grasp1[0] + 0.10, grasp1[1], grasp1[2] + 0.15]), Q1_OPEN_Y)
goto_pose_arm1(np.array([grasp1[0], grasp1[1], grasp1[2] + 0.15]), Q1_OPEN_Y)
goto_pose_arm1(grasp1, Q1_OPEN_Y, z_approach=0.10)
close_gripper_arm1()

# ---------------- Release from Arm 0 and retreat ----------------
open_gripper_arm0()
# Retreat arm0 straight up, then back toward its base, away from arm1
goto_pose_arm0(target0 + np.array([0, 0, 0.10]), Q0_OPEN_Y)
goto_pose_arm0(np.array([target0[0] - 0.15, target0[1], target0[2] + 0.10]), Q0_OPEN_Y)

# Arm 1 holds the hammer by the handle, keeping it inside the height window

# Code block 1
import numpy as np

# Query-only check: the previous block ran without errors. Re-running the full sequence could
# disturb the handover, so only check the hammer state and correct it if needed.
h, q = get_hammer_pose()
h = np.array(h, dtype=float)
print("hammer position:", h, "quat:", q)

# If Arm 1 holds the hammer but its z is outside [0.15, 0.20], shift Arm 1 vertically.
# The adjustment is limited to a few cm and only applies if the hammer is still held near
# the handover point, not dropped or still on the table.
if abs(h[0] - 0.81) < 0.15 and abs(h[1]) < 0.15 and h[2] > 0.05:
    if h[2] < 0.155 or h[2] > 0.195:
        try:
            g1 = np.array(grasp1, dtype=float)
        except NameError:
            g1 = np.array([h[0] + 0.05, h[1], h[2]])
        dz = float(np.clip(0.175 - h[2], -0.04, 0.04))
        goto_pose_arm1(g1 + np.array([0.0, 0.0, dz]), np.array([0.0, 0.0, 1.0, 0.0]))
        h2, _ = get_hammer_pose()
        print("hammer position after correction:", np.array(h2, dtype=float))
    else:
        print("Hammer z within handover window.")
else:
    print("Hammer not near handover location; inspect state.")