# Code block 0
import numpy as np

# Reference quaternions provided by the system
# Arm0 facing down opening along X: aligns with initial Y-oriented hammer
q_arm0_grasp = np.array([0.0, 0.707, 0.707, 0.0])
# Arm0 facing down opening along Y: after -90 deg Z-rotation, hammer aligns with X-axis
q_arm0_handover = np.array([0.0, 1.0, 0.0, 0.0])
# Arm1 facing down opening along Y: grasps the X-aligned hammer handle from above
q_arm1_handover = np.array([0.0, 0.0, 1.0, 0.0])

# 1. Get initial hammer handle pose
hammer_pos, _ = get_hammer_pose()

# Handover height constraint: z must be between 0.15 and 0.20
z_handover = 0.175

# Grasp offset: handle length is 0.15m-0.25m, head is at -Y.
# Grasping at -0.04m along Y places Arm0 safely on the handle towards the head,
# leaving at least 11.5cm of the handle towards +Y free for Arm1.
grasp_pos_arm0 = np.array([hammer_pos[0], hammer_pos[1] - 0.04, hammer_pos[2]])

# 2. Arm0 approaches and grasps hammer
open_gripper_arm0()
# Use z_approach to descend cleanly along Z
goto_pose_arm0(grasp_pos_arm0, q_arm0_grasp, z_approach=0.08)
close_gripper_arm0()

# 3. Lift hammer vertically to the handover height
lift_pos_arm0 = np.array([grasp_pos_arm0[0], grasp_pos_arm0[1], z_handover])
goto_pose_arm0(lift_pos_arm0, q_arm0_grasp)

# 4. Rotate Arm0 in place by -90 deg around Z
# This re-orients the hammer to lie along the X-axis (handle pointing towards +X, i.e., towards Arm1)
goto_pose_arm0(lift_pos_arm0, q_arm0_handover)

# 5. Stepwise translation to handover position near the midpoint of the arms (x ~ 0.81, y = 0.0)
# Arm0 holds the hammer at 4cm behind the handle center along X.
# Setting hammer center at x = 0.81 places Arm0 at x = 0.77.
target_pos_arm0 = np.array([0.77, 0.0, z_handover])
for step in np.linspace(0.25, 1.0, 4):
    waypoint = lift_pos_arm0 + step * (target_pos_arm0 - lift_pos_arm0)
    goto_pose_arm0(waypoint, q_arm0_handover)

# 6. Arm1 prepares and moves to handover grasp position
# Arm1 grasps at x = 0.86 (+0.05m from handle center), maintaining a 9cm buffer (> 8cm minimum)
open_gripper_arm1()
grasp_pos_arm1 = np.array([0.86, 0.0, z_handover])

# Pre-approach above the hammer to avoid horizontal collisions
pre_approach_arm1 = np.array([0.86, 0.0, z_handover + 0.08])
goto_pose_arm1(pre_approach_arm1, q_arm1_handover)
goto_pose_arm1(grasp_pos_arm1, q_arm1_handover)

# 7. Complete handover: Arm1 grasps handle, Arm0 releases and retreats
close_gripper_arm1()
open_gripper_arm0()

# Safe stepwise retreat for Arm0
retreat_pos_arm0 = np.array([0.65, 0.0, z_handover])
goto_pose_arm0(retreat_pos_arm0, q_arm0_handover)