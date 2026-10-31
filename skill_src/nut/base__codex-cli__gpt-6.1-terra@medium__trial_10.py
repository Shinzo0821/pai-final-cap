# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def rotation_from_wxyz(q):
    return R.from_quat([q[1], q[2], q[3], q[0]])

def wxyz_from_rotation(r):
    q = r.as_quat()
    return np.array([q[3], q[0], q[1], q[2]])

nut_pos, nut_quat = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")
block_pos, block_quat = get_object_pose("brown square block")

nut_rot = rotation_from_wxyz(nut_quat)
grasp_rot = rotation_from_wxyz(grasp_quat)
block_rot = rotation_from_wxyz(block_quat)

# Preserve the rigid transform from the nut center to the grasp frame.
center_to_grasp_pos = nut_rot.inv().apply(grasp_pos - nut_pos)
center_to_grasp_rot = nut_rot.inv() * grasp_rot

target_grasp_pos = block_pos + block_rot.apply(center_to_grasp_pos)
target_grasp_rot = block_rot * center_to_grasp_rot
target_grasp_quat = wxyz_from_rotation(target_grasp_rot)

open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()
goto_pose(grasp_pos + np.array([0.0, 0.0, 0.12]), grasp_quat)
goto_pose(target_grasp_pos, target_grasp_quat, z_approach=0.12)
open_gripper()
goto_pose(target_grasp_pos + np.array([0.0, 0.0, 0.12]), target_grasp_quat)
goto_home_joint_position()