# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def rotation_from_wxyz(q):
    q = np.asarray(q)
    return R.from_quat([q[1], q[2], q[3], q[0]])

def wxyz_from_rotation(rotation):
    q = rotation.as_quat()
    return np.array([q[3], q[0], q[1], q[2]])

nut_pos, nut_quat = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")
block_pos, block_quat = get_object_pose("brown square block")

nut_rot = rotation_from_wxyz(nut_quat)
grasp_rot = rotation_from_wxyz(grasp_quat)
block_rot = rotation_from_wxyz(block_quat)

# Fixed transform from nut center to the grasp frame.
nut_to_grasp_pos = nut_rot.inv().apply(np.asarray(grasp_pos) - np.asarray(nut_pos))
nut_to_grasp_rot = nut_rot.inv() * grasp_rot

# Align the nut center and orientation with the target block.
target_grasp_pos = np.asarray(block_pos) + block_rot.apply(nut_to_grasp_pos)
target_grasp_rot = block_rot * nut_to_grasp_rot
target_grasp_quat = wxyz_from_rotation(target_grasp_rot)

open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()
goto_pose(np.asarray(grasp_pos) + np.array([0.0, 0.0, 0.15]), grasp_quat)
goto_pose(target_grasp_pos, target_grasp_quat, z_approach=0.15)
open_gripper()
goto_pose(target_grasp_pos + np.array([0.0, 0.0, 0.15]), target_grasp_quat)
goto_home_joint_position()