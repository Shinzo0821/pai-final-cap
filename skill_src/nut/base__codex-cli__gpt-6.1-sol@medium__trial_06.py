# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation_from_wxyz(q):
    q = np.asarray(q, dtype=float)
    return Rotation.from_quat(q[[1, 2, 3, 0]])

def wxyz_from_rotation(r):
    return r.as_quat()[[3, 0, 1, 2]]

open_gripper()

nut_position, nut_quaternion = get_object_pose("white hollow center of the brown square nut")
grasp_position, grasp_quaternion = sample_grasp_pose("extruded handle of the brown square nut")
block_position, block_quaternion = get_object_pose("brown square block")

nut_position = np.asarray(nut_position, dtype=float)
grasp_position = np.asarray(grasp_position, dtype=float)
block_position = np.asarray(block_position, dtype=float)

nut_rotation = rotation_from_wxyz(nut_quaternion)
grasp_rotation = rotation_from_wxyz(grasp_quaternion)
block_rotation = rotation_from_wxyz(block_quaternion)

# Preserve the full rigid transform from the nut center to the handle grasp.
center_to_grasp_translation = nut_rotation.inv().apply(grasp_position - nut_position)
center_to_grasp_rotation = nut_rotation.inv() * grasp_rotation

goto_pose(grasp_position, grasp_quaternion, z_approach=0.10)
close_gripper()
goto_pose(grasp_position + np.array([0.0, 0.0, 0.15]), grasp_quaternion)

target_grasp_rotation = block_rotation * center_to_grasp_rotation
target_grasp_quaternion = wxyz_from_rotation(target_grasp_rotation)
target_grasp_position = block_position + block_rotation.apply(center_to_grasp_translation)

goto_pose(target_grasp_position + np.array([0.0, 0.0, 0.15]), target_grasp_quaternion)
goto_pose(target_grasp_position, target_grasp_quaternion, z_approach=0.10)
open_gripper()
goto_pose(target_grasp_position + np.array([0.0, 0.0, 0.15]), target_grasp_quaternion)
goto_home_joint_position()