# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def wxyz_to_rot(q):
    return R.from_quat([q[1], q[2], q[3], q[0]])

def rot_to_wxyz(r):
    x, y, z, w = r.as_quat()
    return np.array([w, x, y, z])

def make_T(p, r):
    T = np.eye(4)
    T[:3, :3] = r.as_matrix()
    T[:3, 3] = p
    return T

# Get the current poses of the nut center, the handle grasp, and the peg
nut_pos, nut_quat = get_object_pose('white hollow center of the brown square nut')
grasp_pos, grasp_quat = sample_grasp_pose('extruded handle of the brown square nut')
peg_pos, peg_quat = get_object_pose('brown square block')

r_nut = wxyz_to_rot(nut_quat)
r_grasp = wxyz_to_rot(grasp_quat)
r_peg = wxyz_to_rot(peg_quat)

T_w_nut = make_T(nut_pos, r_nut)
T_w_grasp = make_T(grasp_pos, r_grasp)

# Fixed rigid transform from the nut center to the handle grasp
T_nut_grasp = np.linalg.inv(T_w_nut) @ T_w_grasp

# Align the nut's yaw with the square peg, choosing the smallest rotation modulo 90 degrees
nut_yaw = r_nut.as_euler('xyz')[2]
peg_yaw = r_peg.as_euler('xyz')[2]
d = peg_yaw - nut_yaw
d = (d + np.pi / 4) % (np.pi / 2) - np.pi / 4
r_nut_target = R.from_euler('z', d) * r_nut

# Target nut center: above the peg, at the nut's current resting height plus a small margin
nut_target_pos = np.array([peg_pos[0], peg_pos[1], nut_pos[2] + 0.01])
T_w_nut_target = make_T(nut_target_pos, r_nut_target)

# Corresponding end-effector pose for the target
T_w_grasp_target = T_w_nut_target @ T_nut_grasp
grasp_target_pos = T_w_grasp_target[:3, 3]
grasp_target_quat = rot_to_wxyz(R.from_matrix(T_w_grasp_target[:3, :3]))

# Grasp the handle
goto_home_joint_position()
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.2])
goto_pose(lift_pos, grasp_quat)

# Move above the peg with the aligned orientation
above_target = grasp_target_pos + np.array([0.0, 0.0, 0.2])
goto_pose(above_target, grasp_target_quat)

# Lower straight down onto the peg
goto_pose(grasp_target_pos, grasp_target_quat, z_approach=0.2)

# Release and retreat
open_gripper()
goto_pose(grasp_target_pos + np.array([0.0, 0.0, 0.15]), grasp_target_quat)
goto_home_joint_position()