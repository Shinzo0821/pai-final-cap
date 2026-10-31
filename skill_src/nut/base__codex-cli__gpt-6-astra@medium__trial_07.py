# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation_from_wxyz(q):
    return Rotation.from_quat(np.asarray(q)[[1, 2, 3, 0]]).as_matrix()

def wxyz_from_rotation(r):
    return Rotation.from_matrix(r).as_quat()[[3, 0, 1, 2]]

open_gripper()

nut_position, nut_quaternion = get_object_pose(
    "white hollow center of the brown square nut"
)
grasp_position, grasp_quaternion = sample_grasp_pose(
    "extruded handle of the brown square nut"
)
block_position, block_quaternion = get_object_pose("brown square block")

nut_position = np.asarray(nut_position)
grasp_position = np.asarray(grasp_position)
block_position = np.asarray(block_position)

nut_rotation = rotation_from_wxyz(nut_quaternion)
grasp_rotation = rotation_from_wxyz(grasp_quaternion)
block_rotation = rotation_from_wxyz(block_quaternion)

# Preserve the rigid transform from the nut center to the handle grasp.
relative_position = nut_rotation.T @ (grasp_position - nut_position)
relative_rotation = nut_rotation.T @ grasp_rotation

goto_pose(grasp_position, grasp_quaternion, z_approach=0.10)
close_gripper()

lift_position = grasp_position + np.array([0.0, 0.0, 0.15])
goto_pose(lift_position, grasp_quaternion)

target_grasp_position = block_position + block_rotation @ relative_position
target_grasp_rotation = block_rotation @ relative_rotation
target_grasp_quaternion = wxyz_from_rotation(target_grasp_rotation)

clearance = max(lift_position[2], target_grasp_position[2] + 0.15)
above_target = target_grasp_position.copy()
above_target[2] = clearance
goto_pose(above_target, target_grasp_quaternion)

goto_pose(target_grasp_position, target_grasp_quaternion, z_approach=0.08)
open_gripper()
goto_pose(
    target_grasp_position + np.array([0.0, 0.0, 0.15]),
    target_grasp_quaternion,
)
goto_home_joint_position()