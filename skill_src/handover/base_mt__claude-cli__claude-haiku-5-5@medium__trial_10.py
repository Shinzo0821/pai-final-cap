# Code block 0
import numpy as np

# Quaternions (WXYZ)
Q_ARM0_X = np.array([0.0, 0.707, 0.707, 0.0])  # arm0 down, opening along X (fingers close across handle initially along Y)
Q_ARM0_Y = np.array([0.0, 1.0, 0.0, 0.0])      # arm0 down, opening along Y (after -90 deg yaw, handle lies along X)
Q_ARM1_Y = np.array([0.0, 0.0, 1.0, 0.0])      # arm1 down, opening along Y (fingers close across handle along X)

TRANSPORT_Z = 0.25   # safe travel height above the table
HANDOVER_Z = 0.175   # must stay within 0.15-0.20 during handover
GRIP_OFFSET = 0.05   # grip 5 cm off the handle center, toward the head side (-Y) initially

# Handover geometry (robot0 base frame)
# Midpoint of arm0 (x=0.44) and arm1 (x=1.18) is x=0.81, y=0.0.
# Hammer center target is C = (0.81, 0.0). After the -90 deg yaw about the arm0 grip point,
# the center sits at grip + (0.05, 0). So arm0 grip target G_h = (0.76, 0.0).
# Arm1 grips the far half of the handle at C + (0.05, 0) = (0.86, 0.0).
# Grip separation is 0.10 m, which satisfies the 8 cm buffer.
G_H = np.array([0.76, 0.0, HANDOVER_Z])
ARM1_GRASP = np.array([0.86, 0.0, HANDOVER_Z])
ARM0_RETRACT = np.array([0.60, 0.0, TRANSPORT_Z])

# 1. Open both grippers
open_gripper_arm0()
open_gripper_arm1()

# 2. Locate hammer and pick it with arm0 near the head side of the handle
pos, quat = get_hammer_pose()
pos = np.asarray(pos, dtype=float)
G0 = np.array([pos[0], pos[1] - GRIP_OFFSET, pos[2]])
goto_pose_arm0(G0, Q_ARM0_X, z_approach=0.10)
close_gripper_arm0()

# 3. Lift to transport height at the current location (no rotation yet, avoids table contact)
goto_pose_arm0(np.array([G0[0], G0[1], TRANSPORT_Z]), Q_ARM0_X)

# 4. Yaw the hammer 90 deg about the grip point so the handle points toward arm1 (+X)
#    Rotation is about the TCP, so the grip point G0 stays fixed.
goto_pose_arm0(np.array([G0[0], G0[1], TRANSPORT_Z]), Q_ARM0_Y)

# 5. Translate to the handover area at transport height, then descend to handover height
goto_pose_arm0(np.array([G_H[0], G_H[1], TRANSPORT_Z]), Q_ARM0_Y)
goto_pose_arm0(G_H, Q_ARM0_Y)

# 6. Arm1 approaches from above onto the far half of the handle (not the head)
open_gripper_arm1()
goto_pose_arm1(ARM1_GRASP, Q_ARM1_Y, z_approach=0.08)
close_gripper_arm1()

# 7. Arm0 releases only after arm1 has a firm grip, then retracts upward and away
open_gripper_arm0()
goto_pose_arm0(ARM0_RETRACT, Q_ARM0_Y)

# Code block 1
import numpy as np

# Read-only verification: query the hammer pose without moving either arm.
# The handover code ran without errors, but it never checked the final hammer state.
pos, quat = get_hammer_pose()
pos = np.asarray(pos, dtype=float)
print("hammer position (robot0 frame):", pos)
print("z within 0.15-0.20 success band:", 0.15 <= pos[2] <= 0.20)

# Code block 2
import numpy as np

# Hammer is held by arm1 only (arm0 has released and retracted to x=0.60, z=0.25).
# Observed hammer z = 0.2027 is just above the 0.15-0.20 success band.
# Lower arm1 in small 1 cm steps while it keeps its grip, re-reading the hammer
# pose after each step, and stop once the hammer is near the 0.175 m target.
Q_ARM1_Y = np.array([0.0, 0.0, 1.0, 0.0])
HANDOVER_Z = 0.175
ARM1_X, ARM1_Y = 0.86, 0.0
MAX_STEP = 0.01
TOL = 0.015

arm_z = HANDOVER_Z  # commanded arm1 z, assumed to match the last handover command

for _ in range(6):
    pos, quat = get_hammer_pose()
    pos = np.asarray(pos, dtype=float)
    print("hammer z:", pos[2], "arm1 cmd z:", arm_z)

    err = pos[2] - HANDOVER_Z
    if abs(err) <= TOL:
        break

    # Move arm1 toward the height that places the hammer at HANDOVER_Z, limited per step
    step = np.clip(-err, -MAX_STEP, MAX_STEP)
    arm_z += step
    goto_pose_arm1(np.array([ARM1_X, ARM1_Y, arm_z]), Q_ARM1_Y)

# Final read-only check
pos, quat = get_hammer_pose()
pos = np.asarray(pos, dtype=float)
print("final hammer position (robot0 frame):", pos)
print("z within 0.15-0.20 success band:", 0.15 <= pos[2] <= 0.20)