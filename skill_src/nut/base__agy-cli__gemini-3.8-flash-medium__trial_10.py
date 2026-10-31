# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# 1. Open gripper to prepare for grasping
open_gripper()

# 2. Query poses for the nut handle, nut hollow center, and the target block
handle_pos, handle_quat_wxyz = sample_grasp_pose('extruded handle of the brown square nut')
nut_pos, nut_quat_wxyz = get_object_pose('white hollow center of the brown square nut')
peg_pos, peg_quat_wxyz = get_object_pose('brown square block')

# Helper function to convert wxyz quaternion to scipy Rotation
def quat_wxyz_to_rot(q):
    return R.from_quat([q[1], q[2], q[3], q[0]])

# Helper function to convert scipy Rotation to wxyz quaternion
def rot_to_quat_wxyz(rot):
    q_xyzw = rot.as_quat()
    return np.array([q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]])

# Construct 4x4 transformation matrices in world frame
T_world_nut = np.eye(4)
T_world_nut[:3, :3] = quat_wxyz_to_rot(nut_quat_wxyz).as_matrix()
T_world_nut[:3, 3] = nut_pos

T_world_handle = np.eye(4)
T_world_handle[:3, :3] = quat_wxyz_to_rot(handle_quat_wxyz).as_matrix()
T_world_handle[:3, 3] = handle_pos

# Compute the fixed rigid transformation from the nut center to the handle grasp pose:
# T_nut_handle = T_world_nut^(-1) * T_world_handle
T_nut_handle = np.linalg.inv(T_world_nut) @ T_world_handle

# 3. Grasp the nut by its extruded handle with a vertical approach
goto_pose(handle_pos, handle_quat_wxyz, z_approach=0.1)
close_gripper()

# 4. Lift the nut vertically to clear the surface
lift_pos = handle_pos + np.array([0.0, 0.0, 0.15])
goto_pose(lift_pos, handle_quat_wxyz)

# 5. Compute target end-effector pose for inserting the nut onto the block
# Target nut center pose aligns with the peg pose
T_world_peg = np.eye(4)
T_world_peg[:3, :3] = quat_wxyz_to_rot(peg_quat_wxyz).as_matrix()
T_world_peg[:3, 3] = peg_pos

# Target end-effector pose: T_world_ee_target = T_world_peg * T_nut_handle
T_world_ee_target = T_world_peg @ T_nut_handle

target_pos = T_world_ee_target[:3, 3]
target_rot = R.from_matrix(T_world_ee_target[:3, :3])
target_quat_wxyz = rot_to_quat_wxyz(target_rot)

# 6. Insert the nut onto the block with an approach from above and release
goto_pose(target_pos, target_quat_wxyz, z_approach=0.1)
open_gripper()