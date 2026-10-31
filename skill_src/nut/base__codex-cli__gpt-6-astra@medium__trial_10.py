# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation(q_wxyz):
    return Rotation.from_quat(np.asarray(q_wxyz)[[1, 2, 3, 0]]).as_matrix()

def quaternion(R):
    return Rotation.from_matrix(R).as_quat()[[3, 0, 1, 2]]

open_gripper()

nut_position, nut_quaternion = get_object_pose("white hollow center of the brown square nut")
grasp_position, grasp_quaternion = sample_grasp_pose("extruded handle of the brown square nut")
block_position, block_quaternion = get_object_pose("brown square block")

nut_position = np.asarray(nut_position)
grasp_position = np.asarray(grasp_position)
block_position = np.asarray(block_position)

R_nut = rotation(nut_quaternion)
R_grasp = rotation(grasp_quaternion)
R_block = rotation(block_quaternion)

# Preserve the full rigid transform from the nut center to the handle grasp.
nut_to_grasp_position = R_nut.T @ (grasp_position - nut_position)
nut_to_grasp_rotation = R_nut.T @ R_grasp

goto_pose(grasp_position, grasp_quaternion, z_approach=0.10)
close_gripper()
goto_pose(grasp_position + np.array([0.0, 0.0, 0.15]), grasp_quaternion)

target_grasp_position = block_position + R_block @ nut_to_grasp_position
target_grasp_quaternion = quaternion(R_block @ nut_to_grasp_rotation)

goto_pose(target_grasp_position + np.array([0.0, 0.0, 0.15]), target_grasp_quaternion)
goto_pose(target_grasp_position, target_grasp_quaternion, z_approach=0.10)
open_gripper()
goto_pose(target_grasp_position + np.array([0.0, 0.0, 0.15]), target_grasp_quaternion)
goto_home_joint_position()