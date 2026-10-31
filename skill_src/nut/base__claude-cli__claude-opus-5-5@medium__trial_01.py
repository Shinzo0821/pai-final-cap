# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def to_R(q_wxyz):
    return R.from_quat([q_wxyz[1], q_wxyz[2], q_wxyz[3], q_wxyz[0]])

def to_wxyz(rot):
    q = rot.as_quat()
    return np.array([q[3], q[0], q[1], q[2]])

# Get the nut center pose and the handle grasp pose
nut_pos, nut_q = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_q = sample_grasp_pose("extruded handle of the brown square nut")

R_wn = to_R(nut_q)
R_wg = to_R(grasp_q)

# Fixed transform of the grasp in the nut frame
R_ng = R_wn.inv() * R_wg
p_ng = R_wn.inv().apply(grasp_pos - nut_pos)

# Grasp the handle
open_gripper()
goto_pose(grasp_pos, grasp_q, z_approach=0.12)
close_gripper()

# Lift the nut
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.20])
goto_pose(lift_pos, grasp_q)

# Get the block (peg) pose
block_pos, block_q = get_object_pose("brown square block")
R_wb = to_R(block_q)

# Align the nut yaw with the square block's yaw (modulo 90 deg), with minimal rotation
nut_yaw = R_wn.as_euler("xyz")[2]
block_yaw = R_wb.as_euler("xyz")[2]
d = block_yaw - nut_yaw
d = (d + np.pi / 4) % (np.pi / 2) - np.pi / 4
R_wn_target = R.from_euler("z", d) * R_wn

# Target nut center: centered on the peg, at the peg's height
nut_target_pos = np.array([block_pos[0], block_pos[1], block_pos[2]])

# Compute the corresponding gripper target pose using the fixed nut->grasp transform
R_wg_target = R_wn_target * R_ng
grasp_target_pos = nut_target_pos + R_wn_target.apply(p_ng)
grasp_target_q = to_wxyz(R_wg_target)

# Move above the peg first, then descend straight down to insert
above_pos = grasp_target_pos + np.array([0.0, 0.0, 0.20])
goto_pose(above_pos, grasp_target_q)
goto_pose(grasp_target_pos, grasp_target_q, z_approach=0.20)

# Release the nut and retreat
open_gripper()
goto_pose(grasp_target_pos + np.array([0.0, 0.0, 0.15]), grasp_target_q)
goto_home_joint_position()