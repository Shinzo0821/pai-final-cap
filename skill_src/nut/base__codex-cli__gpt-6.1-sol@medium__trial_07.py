# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation(q_wxyz):
    return Rotation.from_quat(np.asarray(q_wxyz)[[1, 2, 3, 0]]).as_matrix()

def quaternion(matrix):
    return Rotation.from_matrix(matrix).as_quat()[[3, 0, 1, 2]]

nut_position, nut_quaternion = get_object_pose("white hollow center of the brown square nut")
block_position, block_quaternion = get_object_pose("brown square block")
grasp_position, grasp_quaternion = sample_grasp_pose("extruded handle of the brown square nut")

nut_position = np.asarray(nut_position)
block_position = np.asarray(block_position)
grasp_position = np.asarray(grasp_position)

R_nut = rotation(nut_quaternion)
R_block = rotation(block_quaternion)
R_grasp = rotation(grasp_quaternion)

# Preserve the full rigid transform from the nut center to the handle grasp.
nut_to_grasp_position = R_nut.T @ (grasp_position - nut_position)
nut_to_grasp_rotation = R_nut.T @ R_grasp

target_position = block_position + R_block @ nut_to_grasp_position
target_quaternion = quaternion(R_block @ nut_to_grasp_rotation)

open_gripper()
goto_pose(grasp_position, grasp_quaternion, z_approach=0.12)
close_gripper()

clearance_z = max(grasp_position[2], target_position[2]) + 0.18
lift_position = grasp_position.copy()
lift_position[2] = clearance_z
goto_pose(lift_position, grasp_quaternion)

above_target = target_position.copy()
above_target[2] = clearance_z
goto_pose(above_target, target_quaternion)
goto_pose(target_position, target_quaternion, z_approach=0.08)

open_gripper()
goto_pose(above_target, target_quaternion)
goto_home_joint_position()