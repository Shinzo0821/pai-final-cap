# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation(q_wxyz):
    return Rotation.from_quat(np.asarray(q_wxyz)[[1, 2, 3, 0]])

def quaternion(r):
    return r.as_quat()[[3, 0, 1, 2]]

open_gripper()
nut_pos, nut_quat = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")
block_pos, block_quat = get_object_pose("brown square block")

nut_pos = np.asarray(nut_pos)
grasp_pos = np.asarray(grasp_pos)
block_pos = np.asarray(block_pos)

r_nut = rotation(nut_quat)
r_grasp = rotation(grasp_quat)
r_block = rotation(block_quat)

# Preserve the full rigid transform from the nut center to the handle grasp.
local_grasp_offset = r_nut.inv().apply(grasp_pos - nut_pos)
local_grasp_rotation = r_nut.inv() * r_grasp
insert_grasp_pos = block_pos + r_block.apply(local_grasp_offset)
insert_grasp_quat = quaternion(r_block * local_grasp_rotation)

goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()
goto_pose(grasp_pos + np.array([0.0, 0.0, 0.15]), grasp_quat)
goto_pose(insert_grasp_pos + np.array([0.0, 0.0, 0.15]), insert_grasp_quat)
goto_pose(insert_grasp_pos, insert_grasp_quat, z_approach=0.08)
open_gripper()
goto_pose(insert_grasp_pos + np.array([0.0, 0.0, 0.15]), insert_grasp_quat)
goto_home_joint_position()