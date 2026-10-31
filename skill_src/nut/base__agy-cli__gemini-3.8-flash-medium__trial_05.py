# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# Helper functions to convert between pose representation and 4x4 transformation matrices
def pose_to_matrix(pos, quat_wxyz):
    # Convert quaternion from (w, x, y, z) to scipy's (x, y, z, w)
    rot = R.from_quat([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])
    mat = np.eye(4)
    mat[:3, :3] = rot.as_matrix()
    mat[:3, 3] = pos
    return mat

def matrix_to_pose(mat):
    pos = mat[:3, 3]
    rot = R.from_matrix(mat[:3, :3])
    q_xyzw = rot.as_quat()
    # Convert quaternion from scipy's (x, y, z, w) back to (w, x, y, z)
    quat_wxyz = np.array([q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]])
    return pos, quat_wxyz

# 1. Query initial poses for the nut handle, nut center, and the target block
handle_pos, handle_quat = sample_grasp_pose('extruded handle of the brown square nut')
nut_pos, nut_quat = get_object_pose('white hollow center of the brown square nut')
block_pos, block_quat = get_object_pose('brown square block')

# 2. Compute the fixed rigid transformation between nut center and handle grasp
T_world_grasp = pose_to_matrix(handle_pos, handle_quat)
T_world_nut = pose_to_matrix(nut_pos, nut_quat)
T_world_block = pose_to_matrix(block_pos, block_quat)

# Relative transform from nut center to grasp pose: T_nut_grasp = (T_world_nut)^(-1) * T_world_grasp
T_nut_grasp = np.linalg.inv(T_world_nut) @ T_world_grasp

# Desired grasp pose when nut hollow center aligns with the brown square block:
# T_world_grasp_target = T_world_block * T_nut_grasp
T_world_grasp_target = T_world_block @ T_nut_grasp
target_pos, target_quat = matrix_to_pose(T_world_grasp_target)

# 3. Grasp the nut by its handle
open_gripper()
goto_pose(handle_pos, handle_quat, z_approach=0.05)
close_gripper()

# 4. Lift up to ensure clearance during transit
lift_pos = handle_pos.copy()
lift_pos[2] += 0.1
goto_pose(lift_pos, handle_quat)

# 5. Insert the brown square nut onto the brown square block using z_approach
goto_pose(target_pos, target_quat, z_approach=0.05)

# 6. Release gripper after insertion
open_gripper()