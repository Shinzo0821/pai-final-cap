# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation(q):
    return Rotation.from_quat(np.asarray(q)[[1, 2, 3, 0]]).as_matrix()

def quaternion(r):
    return Rotation.from_matrix(r).as_quat()[[3, 0, 1, 2]]

open_gripper()
nut_p, nut_q = get_object_pose("white hollow center of the brown square nut")
grasp_p, grasp_q = sample_grasp_pose("extruded handle of the brown square nut")
block_p, block_q = get_object_pose("brown square block")

nut_p = np.asarray(nut_p)
grasp_p = np.asarray(grasp_p)
block_p = np.asarray(block_p)
nut_r = rotation(nut_q)
grasp_r = rotation(grasp_q)
block_r = rotation(block_q)

# Fixed handle grasp transform expressed in the nut-center frame.
relative_p = nut_r.T @ (grasp_p - nut_p)
relative_r = nut_r.T @ grasp_r

goto_pose(grasp_p, grasp_q, z_approach=0.10)
close_gripper()
goto_pose(grasp_p + np.array([0.0, 0.0, 0.15]), grasp_q)

target_grasp_p = block_p + block_r @ relative_p
target_grasp_q = quaternion(block_r @ relative_r)

goto_pose(target_grasp_p + np.array([0.0, 0.0, 0.15]), target_grasp_q)
goto_pose(target_grasp_p + np.array([0.0, 0.0, 0.05]), target_grasp_q)
goto_pose(target_grasp_p, target_grasp_q)
open_gripper()
goto_pose(target_grasp_p + np.array([0.0, 0.0, 0.15]), target_grasp_q)
goto_home_joint_position()