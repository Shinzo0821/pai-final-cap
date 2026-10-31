# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation_matrix(quaternion_wxyz):
    return Rotation.from_quat(np.asarray(quaternion_wxyz)[[1, 2, 3, 0]]).as_matrix()

def quaternion_wxyz(matrix):
    return Rotation.from_matrix(matrix).as_quat()[[3, 0, 1, 2]]

nut_position, nut_quaternion = get_object_pose("white hollow center of the brown square nut")
block_position, block_quaternion = get_object_pose("brown square block")
grasp_position, grasp_quaternion = sample_grasp_pose("extruded handle of the brown square nut")

nut_position = np.asarray(nut_position)
block_position = np.asarray(block_position)
grasp_position = np.asarray(grasp_position)

nut_rotation = rotation_matrix(nut_quaternion)
grasp_rotation = rotation_matrix(grasp_quaternion)
block_rotation = rotation_matrix(block_quaternion)

nut_to_grasp_position = nut_rotation.T @ (grasp_position - nut_position)
nut_to_grasp_rotation = nut_rotation.T @ grasp_rotation

target_grasp_position = block_position + block_rotation @ nut_to_grasp_position
target_grasp_rotation = block_rotation @ nut_to_grasp_rotation
target_grasp_quaternion = quaternion_wxyz(target_grasp_rotation)

open_gripper()
goto_pose(grasp_position, grasp_quaternion, z_approach=0.10)
close_gripper()

clearance_z = max(grasp_position[2], target_grasp_position[2]) + 0.15
lift_position = grasp_position.copy()
lift_position[2] = clearance_z
goto_pose(lift_position, grasp_quaternion)

approach_position = target_grasp_position.copy()
approach_position[2] = clearance_z
goto_pose(approach_position, target_grasp_quaternion)

for fraction in np.linspace(0.0, 1.0, 16)[1:]:
    position = (1.0 - fraction) * approach_position + fraction * target_grasp_position
    goto_pose(position, target_grasp_quaternion)

open_gripper()
goto_pose(target_grasp_position + np.array([0.0, 0.0, 0.15]), target_grasp_quaternion)
goto_home_joint_position()