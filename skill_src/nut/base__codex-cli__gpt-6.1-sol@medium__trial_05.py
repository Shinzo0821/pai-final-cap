# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation(q):
    return Rotation.from_quat(np.asarray(q)[[1, 2, 3, 0]])

def quaternion(r):
    return r.as_quat()[[3, 0, 1, 2]]

nut_position, nut_quaternion = get_object_pose("white hollow center of the brown square nut")
block_position, block_quaternion = get_object_pose("brown square block")
grasp_position, grasp_quaternion = sample_grasp_pose("extruded handle of the brown square nut")

nut_position = np.asarray(nut_position)
block_position = np.asarray(block_position)
grasp_position = np.asarray(grasp_position)

nut_rotation = rotation(nut_quaternion)
grasp_rotation = rotation(grasp_quaternion)
target_nut_rotation = rotation(block_quaternion)

local_grasp_offset = nut_rotation.inv().apply(grasp_position - nut_position)
relative_grasp_rotation = nut_rotation.inv() * grasp_rotation

target_grasp_position = block_position + target_nut_rotation.apply(local_grasp_offset)
target_grasp_quaternion = quaternion(target_nut_rotation * relative_grasp_rotation)

open_gripper()
goto_pose(grasp_position, grasp_quaternion, z_approach=0.10)
close_gripper()

clearance_z = max(grasp_position[2], target_grasp_position[2], block_position[2]) + 0.15
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