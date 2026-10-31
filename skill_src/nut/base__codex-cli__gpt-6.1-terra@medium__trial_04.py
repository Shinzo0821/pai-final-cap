# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rot(q):
    q = np.asarray(q)
    return Rotation.from_quat([q[1], q[2], q[3], q[0]])

def quat(r):
    q = r.as_quat()
    return np.array([q[3], q[0], q[1], q[2]])

nut_pos, nut_q = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_q = sample_grasp_pose("extruded handle of the brown square nut")
nut_pos = np.asarray(nut_pos)
grasp_pos = np.asarray(grasp_pos)
nut_rot = rot(nut_q)
grasp_rot = rot(grasp_q)

# Transform from nut center to the handle grasp pose.
center_to_grasp_pos = nut_rot.inv().apply(grasp_pos - nut_pos)
center_to_grasp_rot = nut_rot.inv() * grasp_rot

open_gripper()
goto_pose(grasp_pos, grasp_q, z_approach=0.1)
close_gripper()
goto_pose(grasp_pos + np.array([0.0, 0.0, 0.15]), grasp_q)

block_pos, block_q = get_object_pose("brown square block")
block_pos = np.asarray(block_pos)
block_rot = rot(block_q)

# Align the nut center with the block while preserving the grasp transform.
target_grasp_rot = block_rot * center_to_grasp_rot
target_grasp_pos = block_pos + block_rot.apply(center_to_grasp_pos)
target_grasp_q = quat(target_grasp_rot)

goto_pose(target_grasp_pos, target_grasp_q, z_approach=0.15)
open_gripper()
goto_pose(target_grasp_pos + np.array([0.0, 0.0, 0.15]), target_grasp_q)
goto_home_joint_position()