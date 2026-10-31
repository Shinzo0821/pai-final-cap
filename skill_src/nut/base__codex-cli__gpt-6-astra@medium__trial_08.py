# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation(q_wxyz):
    return Rotation.from_quat(np.asarray(q_wxyz)[[1, 2, 3, 0]]).as_matrix()

def quaternion(matrix):
    return Rotation.from_matrix(matrix).as_quat()[[3, 0, 1, 2]]

open_gripper()

nut_p, nut_q = get_object_pose("white hollow center of the brown square nut")
block_p, block_q = get_object_pose("brown square block")
grasp_p, grasp_q = sample_grasp_pose("extruded handle of the brown square nut")

nut_p = np.asarray(nut_p)
block_p = np.asarray(block_p)
grasp_p = np.asarray(grasp_p)

R_nut = rotation(nut_q)
R_grasp = rotation(grasp_q)
R_block = rotation(block_q)

nut_to_grasp_p = R_nut.T @ (grasp_p - nut_p)
nut_to_grasp_R = R_nut.T @ R_grasp

goto_pose(grasp_p, grasp_q, z_approach=0.10)
close_gripper()

clearance_z = max(nut_p[2], block_p[2]) + 0.15
lift_p = grasp_p + np.array([0.0, 0.0, clearance_z - nut_p[2]])
goto_pose(lift_p, grasp_q)

target_grasp_p = block_p + R_block @ nut_to_grasp_p
target_grasp_q = quaternion(R_block @ nut_to_grasp_R)

above_p = target_grasp_p + np.array([0.0, 0.0, clearance_z - block_p[2]])
goto_pose(above_p, target_grasp_q)
goto_pose(target_grasp_p, target_grasp_q, z_approach=0.08)

open_gripper()
goto_pose(target_grasp_p + np.array([0.0, 0.0, 0.15]), target_grasp_q)
goto_home_joint_position()