# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def rotation(q):
    return R.from_quat([q[1], q[2], q[3], q[0]])

def wxyz(r):
    q = r.as_quat()
    return np.array([q[3], q[0], q[1], q[2]])

center_pos, center_q = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_q = sample_grasp_pose("extruded handle of the brown square nut")
block_pos, block_q = get_object_pose("brown square block")

center_rot = rotation(center_q)
grasp_rot = rotation(grasp_q)
block_rot = rotation(block_q)

# Fixed transform from nut center to the grasp frame.
center_to_grasp_pos = center_rot.inv().apply(grasp_pos - center_pos)
center_to_grasp_rot = center_rot.inv() * grasp_rot

open_gripper()
goto_pose(grasp_pos, grasp_q, z_approach=0.1)
close_gripper()

lift_pos = np.array(grasp_pos, dtype=float) + np.array([0.0, 0.0, 0.15])
goto_pose(lift_pos, grasp_q)

# Align the nut center with the block while preserving the grasp transform.
target_grasp_pos = np.asarray(block_pos) + block_rot.apply(center_to_grasp_pos)
target_grasp_rot = block_rot * center_to_grasp_rot
goto_pose(target_grasp_pos, wxyz(target_grasp_rot), z_approach=0.15)
open_gripper()
goto_pose(target_grasp_pos + np.array([0.0, 0.0, 0.15]), wxyz(target_grasp_rot))
goto_home_joint_position()