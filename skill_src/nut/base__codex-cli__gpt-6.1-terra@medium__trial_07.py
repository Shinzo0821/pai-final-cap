# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def rotation_from_wxyz(q):
    q = np.asarray(q)
    return R.from_quat([q[1], q[2], q[3], q[0]])

def wxyz_from_rotation(r):
    q = r.as_quat()
    return np.array([q[3], q[0], q[1], q[2]])

nut_pos, nut_quat = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")
block_pos, block_quat = get_object_pose("brown square block")

nut_pos = np.asarray(nut_pos)
grasp_pos = np.asarray(grasp_pos)
block_pos = np.asarray(block_pos)
nut_rot = rotation_from_wxyz(nut_quat)
grasp_rot = rotation_from_wxyz(grasp_quat)
block_rot = rotation_from_wxyz(block_quat)

# Fixed transform from the nut center to the gripper grasp pose.
center_to_gripper_pos = nut_rot.inv().apply(grasp_pos - nut_pos)
center_to_gripper_rot = nut_rot.inv() * grasp_rot

target_gripper_pos = block_pos + block_rot.apply(center_to_gripper_pos)
target_gripper_rot = block_rot * center_to_gripper_rot
target_gripper_quat = wxyz_from_rotation(target_gripper_rot)

open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()
goto_pose(grasp_pos + np.array([0.0, 0.0, 0.15]), grasp_quat)
goto_pose(target_gripper_pos, target_gripper_quat, z_approach=0.15)
open_gripper()
goto_pose(target_gripper_pos + np.array([0.0, 0.0, 0.15]), target_gripper_quat)
goto_home_joint_position()