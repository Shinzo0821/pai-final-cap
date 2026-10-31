# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation_from_wxyz(q):
    return Rotation.from_quat(np.asarray(q)[[1, 2, 3, 0]]).as_matrix()

def quaternion_wxyz(R):
    return Rotation.from_matrix(R).as_quat()[[3, 0, 1, 2]]

nut_position, nut_quaternion = get_object_pose("white hollow center of the brown square nut")
block_position, block_quaternion = get_object_pose("brown square block")
grasp_position, grasp_quaternion = sample_grasp_pose("extruded handle of the brown square nut")

nut_position = np.asarray(nut_position)
block_position = np.asarray(block_position)
grasp_position = np.asarray(grasp_position)

R_nut = rotation_from_wxyz(nut_quaternion)
R_grasp = rotation_from_wxyz(grasp_quaternion)
R_block = rotation_from_wxyz(block_quaternion)

handle_offset_in_nut = R_nut.T @ (grasp_position - nut_position)
handle_rotation_in_nut = R_nut.T @ R_grasp

target_grasp_position = block_position + R_block @ handle_offset_in_nut
target_grasp_rotation = R_block @ handle_rotation_in_nut
target_grasp_quaternion = quaternion_wxyz(target_grasp_rotation)

open_gripper()
goto_pose(grasp_position, grasp_quaternion, z_approach=0.10)
close_gripper()

lift_position = grasp_position + np.array([0.0, 0.0, 0.15])
goto_pose(lift_position, grasp_quaternion)

above_target = target_grasp_position + np.array([0.0, 0.0, 0.15])
goto_pose(above_target, target_grasp_quaternion)
goto_pose(target_grasp_position, target_grasp_quaternion, z_approach=0.10)

open_gripper()
goto_pose(above_target, target_grasp_quaternion)
goto_home_joint_position()