# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def wxyz_to_rot(q):
    return R.from_quat([q[1], q[2], q[3], q[0]])

def rot_to_wxyz(r):
    x, y, z, w = r.as_quat()
    return np.array([w, x, y, z])

# Start from home with an open gripper
goto_home_joint_position()
open_gripper()

# Nut center pose and handle grasp pose, sampled while the nut is still at rest
nut_pos, nut_quat = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")

R_nut = wxyz_to_rot(nut_quat)
R_ee = wxyz_to_rot(grasp_quat)

# Fixed rigid transform from end-effector to nut center, expressed in the EE frame
R_ee_to_nut = R_ee.inv() * R_nut
p_ee_to_nut = R_ee.inv().apply(nut_pos - grasp_pos)

# Grasp the handle
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the nut straight up
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.2])
goto_pose(lift_pos, grasp_quat)

# Target block / peg pose
peg_pos, peg_quat = get_object_pose("brown square block")
R_peg = wxyz_to_rot(peg_quat)

# Align the nut yaw to the square peg yaw (modulo 90 deg), taking the smallest rotation
nut_yaw = R_nut.as_euler("xyz")[2]
peg_yaw = R_peg.as_euler("xyz")[2]
d_yaw = peg_yaw - nut_yaw
d_yaw = (d_yaw + np.pi / 4) % (np.pi / 2) - np.pi / 4
R_yaw = R.from_euler("z", d_yaw)

# Desired nut center pose: centered on the peg, resting near its original table height
R_nut_target = R_yaw * R_nut
nut_target_pos = np.array([peg_pos[0], peg_pos[1], nut_pos[2] + 0.01])

# Convert the desired nut pose into an EE pose using the fixed transform
R_ee_target = R_nut_target * R_ee_to_nut.inv()
ee_target_pos = nut_target_pos - R_ee_target.apply(p_ee_to_nut)
ee_target_quat = rot_to_wxyz(R_ee_target)

# Move above the peg first, then descend vertically to insert
above_pos = ee_target_pos + np.array([0.0, 0.0, 0.2])
goto_pose(above_pos, ee_target_quat)
goto_pose(ee_target_pos, ee_target_quat, z_approach=0.15)

# Release the nut and retreat upward
open_gripper()
goto_pose(ee_target_pos + np.array([0.0, 0.0, 0.15]), ee_target_quat)
goto_home_joint_position()