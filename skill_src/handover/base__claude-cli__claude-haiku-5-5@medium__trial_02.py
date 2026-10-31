# Code block 0
# Handover plan: Arm0 grasps the handle, rotates the hammer so the handle points toward Arm1, and transfers it at z=0.175 m.
# Arm1 grasps the handle, and Arm0 releases and retracts.
# Assumptions: handle center from get_hammer_pose(); handle half-length >= 0.075 m.
# Grasp points are offset +/-0.045 m from the midpoint (x=0.81), giving 0.09 m gripper separation (>= 8 cm buffer).
# The handover midpoint may lie over the central gap; verify table coverage before running.
import numpy as np

HANDOVER_Z = 0.175
MID_X = 0.81
ARM0_HANDOVER = np.array([MID_X - 0.045, 0.0, HANDOVER_Z])   # handle, arm0 side
ARM1_HANDOVER = np.array([MID_X + 0.045, 0.0, HANDOVER_Z])   # handle, arm1 side

# Quaternions (WXYZ)
Q_ARM0_GRASP = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)  # facing down, opening along X
Q_ARM0_HANDOVER = np.array([0.0, 1.0, 0.0, 0.0])              # facing down, opening along Y (hammer rotated -90 deg about Z so handle points +X)
Q_ARM1_DOWN = np.array([0.0, 0.0, 1.0, 0.0])                  # facing down, opening along Y

# 1. Locate hammer and open both grippers
hammer_pos, hammer_quat = get_hammer_pose()
open_gripper_arm0()
open_gripper_arm1()

# 2. Arm0 grasps the handle middle from above (z approach for precision)
goto_pose_arm0(hammer_pos, Q_ARM0_GRASP, z_approach=0.08)
close_gripper_arm0()

# 3. Lift the hammer to handover height at its current XY
lift_pos = np.array([hammer_pos[0], hammer_pos[1], HANDOVER_Z])
goto_pose_arm0(lift_pos, Q_ARM0_GRASP)

# 4. Rotate the hammer in place (in air) so the handle points toward Arm1
goto_pose_arm0(lift_pos, Q_ARM0_HANDOVER)

# 5. Translate stepwise toward the midpoint, staying at handover height
goto_pose_arm0(np.array([0.60, 0.0, HANDOVER_Z]), Q_ARM0_HANDOVER)
goto_pose_arm0(ARM0_HANDOVER, Q_ARM0_HANDOVER)

# 6. Arm1 moves to a safe staging point on its side, well clear of Arm0
goto_pose_arm1(np.array([0.95, 0.0, 0.30]), Q_ARM1_DOWN)

# 7. Arm1 descends onto the handle (handle side, not head) with a z approach
open_gripper_arm1()
goto_pose_arm1(ARM1_HANDOVER, Q_ARM1_DOWN, z_approach=0.10)
close_gripper_arm1()

# 8. Arm0 releases the hammer, then retracts upward before moving away
open_gripper_arm0()
goto_pose_arm0(np.array([MID_X - 0.045, 0.0, 0.30]), Q_ARM0_HANDOVER)
goto_pose_arm0(np.array([0.55, 0.0, 0.30]), Q_ARM0_HANDOVER)

# Arm1 now holds the hammer by the handle at z ~= 0.175 m.