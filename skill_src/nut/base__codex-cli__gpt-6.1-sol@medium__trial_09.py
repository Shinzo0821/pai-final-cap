# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation_from_wxyz(q):
    return Rotation.from_quat(np.asarray(q)[[1, 2, 3, 0]]).as_matrix()

def wxyz_from_rotation(r):
    return Rotation.from_matrix(r).as_quat()[[3, 0, 1, 2]]

open_gripper()

nut_position, nut_quaternion = get_object_pose("white hollow center of the brown square nut")
grasp_position, grasp_quaternion = sample_grasp_pose("extruded handle of the brown square nut")
block_position, block_quaternion = get_object_pose("brown square block")

nut_position = np.asarray(nut_position)
grasp_position = np.asarray(grasp_position)
block_position = np.asarray(block_position)

nut_rotation = rotation_from_wxyz(nut_quaternion)
grasp_rotation = rotation_from_wxyz(grasp_quaternion)
block_rotation = rotation_from_wxyz(block_quaternion)

nut_to_grasp_position = nut_rotation.T @ (grasp_position - nut_position)
nut_to_grasp_rotation = nut_rotation.T @ grasp_rotation

goto_pose(grasp_position, grasp_quaternion, z_approach=0.10)
close_gripper()

lift = np.array([0.0, 0.0, 0.15])
goto_pose(grasp_position + lift, grasp_quaternion)

target_grasp_rotation = block_rotation @ nut_to_grasp_rotation
target_grasp_quaternion = wxyz_from_rotation(target_grasp_rotation)
target_grasp_position = block_position + block_rotation @ nut_to_grasp_position

goto_pose(target_grasp_position + lift, target_grasp_quaternion)
goto_pose(target_grasp_position, target_grasp_quaternion, z_approach=0.08)

open_gripper()
goto_pose(target_grasp_position + lift, target_grasp_quaternion)
goto_home_joint_position()