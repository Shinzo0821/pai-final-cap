# Code block 0
import numpy as np

# 1. Initialize both grippers to open state
open_gripper_arm0()
open_gripper_arm1()

# 2. Get the initial pose of the hammer
# hammer_pos corresponds to the center of the handle.
# The hammer lies flat along the Y-axis: handle towards +Y, head towards -Y.
hammer_pos, _ = get_hammer_pose()

# Reference orientations:
# Arm0 facing down opening along X-axis (to grasp hammer aligned along Y-axis)
q0_pick = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down opening along Y-axis (holding hammer aligned along X-axis)
q0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down opening along Y-axis (to grasp hammer handle aligned along X-axis)
q1_handover = np.array([0.0, 0.0, 1.0, 0.0])

# 3. Arm0 grasp planning:
# Grasp the handle slightly towards the head (-Y offset from handle center)
# to leave sufficient handle length (+Y) free for Arm1 to grasp later.
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] - 0.03, hammer_pos[2]])

# Approach vertically from above to avoid collision with table or hammer
goto_pose_arm0(grasp_pos_arm0, q0_pick, z_approach=0.10)
close_gripper_arm0()

# 4. Lift the hammer vertically to clear the table surface
lift_pos_arm0 = np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], 0.25])
goto_pose_arm0(lift_pos_arm0, q0_pick)

# 5. Decompose motions: Rotate in place before translating
# Rotating Arm0 gripper 90 degrees around Z orients the hammer along the X-axis.
# Head is oriented towards -X (Arm0 side), handle extends towards +X (Arm1 side).
goto_pose_arm0(lift_pos_arm0, q0_handover)

# 6. Translate to handover position stepwise:
# Handover must occur near the midpoint between Arm0 (x~0.44) and Arm1 (x~1.18), x_mid ~ 0.81.
# Handover Z must be between 0.15 and 0.20 (chosen z = 0.175).
arm0_handover_pos = np.array([0.73, 0.0, 0.175])

# Translate in XY at safe lift height first, then descend to handover Z
goto_pose_arm0(np.array([arm0_handover_pos[0], arm0_handover_pos[1], 0.25]), q0_handover)
goto_pose_arm0(arm0_handover_pos, q0_handover)

# 7. Arm1 approaches the hammer handle:
# With Arm0 at x = 0.73, the handle extends from x = 0.73 past x = 0.88.
# Target Arm1 grasp at x = 0.84, providing an 11cm separation buffer (> 8cm requirement)
# and ensuring Arm1 grasps the handle, not the head.
arm1_handover_pos = np.array([0.84, 0.0, 0.175])

# Approach vertically using z_approach to avoid intermediate collisions
goto_pose_arm1(arm1_handover_pos, q1_handover, z_approach=0.10)

# 8. Transfer ownership: Arm1 closes gripper on handle, Arm0 releases
close_gripper_arm1()
open_gripper_arm0()

# 9. Retract Arm0 safely away from Arm1 and the hammer
goto_pose_arm0(np.array([0.55, 0.0, 0.25]), q0_handover)