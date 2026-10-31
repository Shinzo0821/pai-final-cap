# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def to_R(q_wxyz):
    return R.from_quat([q_wxyz[1], q_wxyz[2], q_wxyz[3], q_wxyz[0]])

def to_wxyz(rot):
    q = rot.as_quat()
    return np.array([q[3], q[0], q[1], q[2]])

def make_T(p, rot):
    T = np.eye(4)
    T[:3, :3] = rot.as_matrix()
    T[:3, 3] = p
    return T

open_gripper()

# Grasp pose on the handle, and the pose of the nut center
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")
nut_pos, nut_quat = get_object_pose("white hollow center of the brown square nut")

# Fixed rigid transform from the nut center to the gripper
T_w_grasp = make_T(grasp_pos, to_R(grasp_quat))
T_w_nut = make_T(nut_pos, to_R(nut_quat))
T_nut_grasp = np.linalg.inv(T_w_nut) @ T_w_grasp

# Grasp the handle
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.2
goto_pose(lift_pos, grasp_quat)

# Peg pose
peg_pos, peg_quat = get_object_pose("brown square block")

# Align the nut yaw to the peg yaw (square, so symmetric every 90 degrees)
nut_yaw = to_R(nut_quat).as_euler("xyz")[2]
peg_yaw = to_R(peg_quat).as_euler("xyz")[2]
delta = peg_yaw - nut_yaw
delta = (delta + np.pi / 4) % (np.pi / 2) - np.pi / 4

target_nut_rot = R.from_euler("z", delta) * to_R(nut_quat)

# Target nut center: above the peg in x/y, at roughly its original resting height
target_nut_pos = np.array([peg_pos[0], peg_pos[1], nut_pos[2] + 0.02])
T_w_nut_target = make_T(target_nut_pos, target_nut_rot)
T_w_grasp_target = T_w_nut_target @ T_nut_grasp

target_grasp_pos = T_w_grasp_target[:3, 3]
target_grasp_quat = to_wxyz(R.from_matrix(T_w_grasp_target[:3, :3]))

# Move above the peg first, then descend to insert
above_pos = target_grasp_pos.copy()
above_pos[2] += 0.2
goto_pose(above_pos, target_grasp_quat)
goto_pose(target_grasp_pos, target_grasp_quat, z_approach=0.2)

# Release the nut and retract
open_gripper()
retreat_pos = target_grasp_pos.copy()
retreat_pos[2] += 0.15
goto_pose(retreat_pos, target_grasp_quat)
goto_home_joint_position()