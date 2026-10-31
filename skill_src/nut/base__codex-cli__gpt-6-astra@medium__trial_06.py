# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

def rotation(q_wxyz):
    return Rotation.from_quat(np.asarray(q_wxyz)[[1, 2, 3, 0]])

nut_p, nut_q = get_object_pose("white hollow center of the brown square nut")
grasp_p, grasp_q = sample_grasp_pose("extruded handle of the brown square nut")
block_p, block_q = get_object_pose("brown square block")

nut_p = np.asarray(nut_p)
grasp_p = np.asarray(grasp_p)
block_p = np.asarray(block_p)

nut_r = rotation(nut_q)
grasp_r = rotation(grasp_q)
block_r = rotation(block_q)

# Preserve the rigid nut-center-to-gripper transform.
relative_p = nut_r.inv().apply(grasp_p - nut_p)
relative_r = nut_r.inv() * grasp_r

target_p = block_p + block_r.apply(relative_p)
target_r = block_r * relative_r
target_q = target_r.as_quat()[[3, 0, 1, 2]]

open_gripper()
goto_pose(grasp_p, grasp_q, z_approach=0.10)
close_gripper()

clearance_z = max(grasp_p[2], target_p[2]) + 0.15
lift_p = grasp_p.copy()
lift_p[2] = clearance_z
goto_pose(lift_p, grasp_q)

above_p = target_p.copy()
above_p[2] = clearance_z
goto_pose(above_p, target_q)
goto_pose(target_p, target_q, z_approach=0.06)

open_gripper()
goto_pose(above_p, target_q)
goto_home_joint_position()