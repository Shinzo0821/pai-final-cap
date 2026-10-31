# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# Helper: quaternion wxyz -> scipy Rotation
def quat_to_rot(q_wxyz):
    return R.from_quat([q_wxyz[1], q_wxyz[2], q_wxyz[3], q_wxyz[0]])

def rot_to_quat(rot):
    x, y, z, w = rot.as_quat()
    return np.array([w, x, y, z])

# Get nut center pose and handle grasp pose
nut_pos, nut_quat = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")

# Get the peg (block) pose
peg_pos, peg_quat = get_object_pose("brown square block")

# Fixed rigid transform from nut center frame to grasp (EE) frame
R_nut = quat_to_rot(nut_quat)
R_grasp = quat_to_rot(grasp_quat)
R_nut_to_grasp = R_nut.inv() * R_grasp
p_nut_to_grasp = R_nut.inv().apply(grasp_pos - nut_pos)

# Grasp the nut by its handle
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift up
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Target nut center pose: same orientation as currently held (keep nut level, no yaw change
# unless needed), positioned above the peg. Keep nut orientation to avoid IK issues; square
# alignment is assumed from current nut yaw matching peg yaw (adjust yaw if needed).
R_peg = quat_to_rot(peg_quat)
# Align nut yaw to peg yaw while keeping nut roll/pitch from its current orientation
nut_yaw = R_nut.as_euler("xyz")[2]
peg_yaw = R_peg.as_euler("xyz")[2]
# Square nut has 90-degree symmetry; pick smallest yaw correction
dyaw = (peg_yaw - nut_yaw + np.pi / 4) % (np.pi / 2) - np.pi / 4
R_nut_target = R.from_euler("z", dyaw) * R_nut

# Desired nut center position: directly above the peg, then lowered onto it
nut_target_pos = np.array([peg_pos[0], peg_pos[1], peg_pos[2] + 0.02])

# Compute corresponding EE pose from the fixed rigid transform
ee_target_rot = R_nut_target * R_nut_to_grasp
ee_target_pos = nut_target_pos + R_nut_target.apply(p_nut_to_grasp)
ee_target_quat = rot_to_quat(ee_target_rot)

# Move above the peg and insert the nut
goto_pose(ee_target_pos, ee_target_quat, z_approach=0.15)

# Release and retreat
open_gripper()
retreat_pos = ee_target_pos.copy()
retreat_pos[2] += 0.15
goto_pose(retreat_pos, ee_target_quat)
goto_home_joint_position()