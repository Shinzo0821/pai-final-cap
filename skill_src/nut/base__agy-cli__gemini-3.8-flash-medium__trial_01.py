# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def pose_to_matrix(pos, quat_wxyz):
    T = np.eye(4)
    # scipy Rotation expects quaternion in (x, y, z, w) order
    T[:3, :3] = R.from_quat([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]]).as_matrix()
    T[:3, 3] = pos
    return T

def matrix_to_pose(T):
    pos = T[:3, 3]
    rot = R.from_matrix(T[:3, :3])
    q_xyzw = rot.as_quat()
    quat_wxyz = np.array([q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]])
    return pos, quat_wxyz

# 1. Open gripper to prepare for grasp
open_gripper()

# 2. Get poses of handle, nut center, and the target block
handle_pos, handle_quat = sample_grasp_pose('extruded handle of the brown square nut')
nut_pos, nut_quat = get_object_pose('white hollow center of the brown square nut')
block_pos, block_quat = get_object_pose('brown square block')

# 3. Move to grasp the handle with a vertical approach offset
goto_pose(handle_pos, handle_quat, z_approach=0.05)
close_gripper()

# 4. Lift the nut up after grasping to clear the table
lift_pos = handle_pos + np.array([0.0, 0.0, 0.15])
goto_pose(lift_pos, handle_quat)

# 5. Compute the rigid transform between the nut center and the handle grasp pose
T_handle = pose_to_matrix(handle_pos, handle_quat)
T_nut = pose_to_matrix(nut_pos, nut_quat)
T_block = pose_to_matrix(block_pos, block_quat)

# Relative transform from nut center to end-effector grasp pose
T_nut_to_ee = np.linalg.inv(T_nut) @ T_handle

# Target end-effector pose when nut center aligns with the block pose
T_target_ee = T_block @ T_nut_to_ee
target_pos, target_quat = matrix_to_pose(T_target_ee)

# 6. Insert the nut onto the block with vertical approach from above
goto_pose(target_pos, target_quat, z_approach=0.1)

# 7. Release the nut
open_gripper()