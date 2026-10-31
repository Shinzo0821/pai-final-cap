# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation_from_wxyz(q):
    return Rotation.from_quat(np.asarray(q)[[1, 2, 3, 0]])

def quaternion_wxyz(r):
    return r.as_quat()[[3, 0, 1, 2]]

nut_position, nut_quaternion = get_object_pose("white hollow center of the brown square nut")
grasp_position, grasp_quaternion = sample_grasp_pose("extruded handle of the brown square nut")
block_position, block_quaternion = get_object_pose("brown square block")

nut_position = np.asarray(nut_position)
grasp_position = np.asarray(grasp_position)
block_position = np.asarray(block_position)

nut_rotation = rotation_from_wxyz(nut_quaternion)
grasp_rotation = rotation_from_wxyz(grasp_quaternion)
block_rotation = rotation_from_wxyz(block_quaternion)

nut_to_grasp_position = nut_rotation.inv().apply(grasp_position - nut_position)
nut_to_grasp_rotation = nut_rotation.inv() * grasp_rotation

target_grasp_position = block_position + block_rotation.apply(nut_to_grasp_position)
target_grasp_rotation = block_rotation * nut_to_grasp_rotation
target_grasp_quaternion = quaternion_wxyz(target_grasp_rotation)

open_gripper()
goto_pose(grasp_position, grasp_quaternion, z_approach=0.10)
close_gripper()

clearance_z = max(grasp_position[2], target_grasp_position[2]) + 0.15
lift_position = grasp_position.copy()
lift_position[2] = clearance_z
goto_pose(lift_position, grasp_quaternion)

above_target = target_grasp_position.copy()
above_target[2] = clearance_z
goto_pose(above_target, target_grasp_quaternion)
goto_pose(target_grasp_position, target_grasp_quaternion, z_approach=0.08)

open_gripper()
goto_pose(above_target, target_grasp_quaternion)
goto_home_joint_position()