# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def pose_to_matrix(position, quat_wxyz):
    # Convert to homogeneous transformation matrix
    # scipy expects [x, y, z, w] (xyzw)
    quat_xyzw = np.array([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])
    rot = R.from_quat(quat_xyzw)
    mat = np.eye(4)
    mat[:3, :3] = rot.as_matrix()
    mat[:3, 3] = position
    return mat

def matrix_to_pose(mat):
    position = mat[:3, 3]
    rot = R.from_matrix(mat[:3, :3])
    quat_xyzw = rot.as_quat()
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])
    return position, quat_wxyz

def invert_transform(mat):
    inv_rot = mat[:3, :3].T
    inv_trans = -inv_rot @ mat[:3, 3]
    inv_mat = np.eye(4)
    inv_mat[:3, :3] = inv_rot
    inv_mat[:3, 3] = inv_trans
    return inv_mat

# 1. Open gripper
open_gripper()

# 2. Sample grasp pose on the handle
handle_pos, handle_quat = sample_grasp_pose("extruded handle of the brown square nut")
# Approach from above (10 cm)
goto_pose(handle_pos, handle_quat, z_approach=0.10)

# 3. Close gripper to grasp the nut
close_gripper()

# 4. Lift the grasped nut a bit
goto_pose(handle_pos, handle_quat, z_approach=0.20)

# 5. Get the fixed transform from handle pose to nut center pose
nut_center_pos, nut_center_quat = get_object_pose("white hollow center of the brown square nut")
T_handle = pose_to_matrix(handle_pos, handle_quat)
T_nut = pose_to_matrix(nut_center_pos, nut_center_quat)
T_handle_to_nut = invert_transform(T_handle) @ T_nut
T_nut_to_handle = invert_transform(T_handle_to_nut)

# 6. Determine target nut pose (the insertion location on the brown square block)
target_block_pos, target_block_quat = get_object_pose("brown square block")
# Assume we want the nut centered on the block surface
T_target_nut = pose_to_matrix(target_block_pos, target_block_quat)

# 7. Compute the required handle pose to place the nut at the target
T_target_handle = T_target_nut @ T_nut_to_handle
target_handle_pos, target_handle_quat = matrix_to_pose(T_target_handle)

# 8. Move above the target handle pose, then descend
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.10)   # above
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.00)   # insert

# 9. Release the nut
open_gripper()

# 10. Retract upward slightly
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.10)

# 11. Return to home position
goto_home_joint_position()