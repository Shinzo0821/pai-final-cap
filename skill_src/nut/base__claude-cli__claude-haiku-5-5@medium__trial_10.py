# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def to_mat(pos, quat_wxyz):
    # Convert position + WXYZ quaternion into a 4x4 homogeneous transform
    q_xyzw = np.array([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])
    T = np.eye(4)
    T[:3, :3] = R.from_quat(q_xyzw).as_matrix()
    T[:3, 3] = np.asarray(pos, dtype=float)
    return T

def from_mat(T):
    # Convert 4x4 homogeneous transform back to position + WXYZ quaternion
    q_xyzw = R.from_matrix(T[:3, :3]).as_quat()
    quat_wxyz = np.array([q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]])
    return T[:3, 3].copy(), quat_wxyz / np.linalg.norm(quat_wxyz)

# Start from a known safe configuration with the gripper open
goto_home_joint_position()
open_gripper()

# 1) Query the nut's object center pose and the handle grasp pose
center_pos, center_quat = get_object_pose('white hollow center of the brown square nut')
T_world_center = to_mat(center_pos, center_quat)

grasp_pos, grasp_quat = sample_grasp_pose('extruded handle of the brown square nut')
T_world_handle = to_mat(grasp_pos, grasp_quat)

# 2) The center-to-handle transform is rigid, so compute it once from the current poses
T_center_handle = np.linalg.inv(T_world_center) @ T_world_handle

# 3) Query the peg (brown square block) pose and compute the target nut-center pose
block_pos, block_quat = get_object_pose('brown square block')
T_world_block = to_mat(block_pos, block_quat)

# Place the nut center directly over the block, with a vertical hover offset for the approach
hover_offset = 0.10  # meters
T_target_center = T_world_block.copy()
T_target_center[2, 3] += hover_offset

# Target handle pose such that the nut center lands on the peg
T_target_handle = T_target_center @ T_center_handle

# 4) Grasp the nut by its handle
grasp_p, grasp_q = from_mat(T_world_handle)
goto_pose(grasp_p, grasp_q, z_approach=0.10)
close_gripper()

# Lift the nut straight up before transporting
lift_p = grasp_p.copy()
lift_p[2] += 0.10
goto_pose(lift_p, grasp_q)

# 5) Move above the peg, then lower the nut onto it
above_p, above_q = from_mat(T_target_handle)
goto_pose(above_p, above_q, z_approach=0.05)

insert_p, insert_q = from_mat(T_target_handle)
insert_p[2] -= hover_offset  # drop the nut down onto the peg
goto_pose(insert_p, insert_q)

# 6) Release the nut and retreat upward
open_gripper()

retreat_p = insert_p.copy()
retreat_p[2] += 0.10
goto_pose(retreat_p, insert_q)

goto_home_joint_position()