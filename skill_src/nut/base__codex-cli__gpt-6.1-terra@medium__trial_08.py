# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def rotation_from_wxyz(q):
    return R.from_quat([q[1], q[2], q[3], q[0]])

def wxyz_from_rotation(r):
    q = r.as_quat()
    return np.array([q[3], q[0], q[1], q[2]])

nut_pos, nut_q = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_q = sample_grasp_pose("extruded handle of the brown square nut")
block_pos, block_q = get_object_pose("brown square block")

nut_rot = rotation_from_wxyz(nut_q)
grasp_rot = rotation_from_wxyz(grasp_q)
block_rot = rotation_from_wxyz(block_q)

# Fixed transform from nut center to the grasp pose.
nut_to_grasp_pos = nut_rot.inv().apply(grasp_pos - nut_pos)
nut_to_grasp_rot = nut_rot.inv() * grasp_rot

# Align the nut center and orientation with the block.
target_grasp_pos = block_pos + block_rot.apply(nut_to_grasp_pos)
target_grasp_rot = block_rot * nut_to_grasp_rot
target_grasp_q = wxyz_from_rotation(target_grasp_rot)

open_gripper()
goto_pose(grasp_pos, grasp_q, z_approach=0.1)
close_gripper()
goto_pose(grasp_pos + np.array([0.0, 0.0, 0.15]), grasp_q)
goto_pose(target_grasp_pos, target_grasp_q, z_approach=0.15)
open_gripper()
goto_pose(target_grasp_pos + np.array([0.0, 0.0, 0.15]), target_grasp_q)
goto_home_joint_position()