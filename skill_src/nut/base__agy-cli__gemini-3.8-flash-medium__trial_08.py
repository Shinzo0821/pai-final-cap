# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def pose_to_matrix(pos, quat_wxyz):
    T = np.eye(4)
    # Scipy expects quaternion in [x, y, z, w] format
    quat_xyzw = np.array([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])
    T[:3, :3] = R.from_quat(quat_xyzw).as_matrix()
    T[:3, 3] = pos
    return T

def matrix_to_pose(T):
    pos = T[:3, 3]
    quat_xyzw = R.from_matrix(T[:3, :3]).as_quat()
    # Convert back to [w, x, y, z] format
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])
    return pos, quat_wxyz

# 1. Get current object poses and grasp pose
nut_center_pos, nut_center_quat = get_object_pose('white hollow center of the brown square nut')
grasp_pos, grasp_quat = sample_grasp_pose('extruded handle of the brown square nut')
block_pos, block_quat = get_object_pose('brown square block')

# 2. Compute the rigid transformation between the nut's center and the handle grasp pose
T_world_nut = pose_to_matrix(nut_center_pos, nut_center_quat)
T_world_grasp = pose_to_matrix(grasp_pos, grasp_quat)
T_nut_grasp = np.linalg.inv(T_world_nut) @ T_world_grasp

# 3. Compute target grasp pose when the nut center is aligned with the brown square block
T_world_block = pose_to_matrix(block_pos, block_quat)
T_world_target_grasp = T_world_block @ T_nut_grasp
target_grasp_pos, target_grasp_quat = matrix_to_pose(T_world_target_grasp)

# 4. Grasp the brown square nut by its extruded handle
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.08)
close_gripper()

# 5. Lift the nut to avoid collisions
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.15])
goto_pose(lift_pos, grasp_quat)

# 6. Insert the nut onto the brown square block
goto_pose(target_grasp_pos, target_grasp_quat, z_approach=0.08)

# 7. Release and retreat
open_gripper()
retract_pos = target_grasp_pos + np.array([0.0, 0.0, 0.15])
goto_pose(retract_pos, target_grasp_quat)
goto_home_joint_position()