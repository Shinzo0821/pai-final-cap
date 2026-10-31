# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def pose_to_matrix(pos, quat_wxyz):
    T = np.eye(4)
    quat_xyzw = np.array([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])
    T[:3, :3] = R.from_quat(quat_xyzw).as_matrix()
    T[:3, 3] = pos
    return T

def matrix_to_pose(T):
    pos = T[:3, 3]
    rot = R.from_matrix(T[:3, :3])
    quat_xyzw = rot.as_quat()
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])
    return pos, quat_wxyz

# 1. Open the gripper before approaching
open_gripper()

# 2. Get the hollow center pose of the nut and the grasp pose on the handle
nut_pos, nut_quat = get_object_pose('white hollow center of the brown square nut')
grasp_pos, grasp_quat = sample_grasp_pose('extruded handle of the brown square nut')

# 3. Approach and grasp the handle
goto_pose(grasp_pos, grasp_quat, z_approach=0.08)
close_gripper()

# 4. Lift up to safely transport the nut
goto_pose(grasp_pos + np.array([0.0, 0.0, 0.15]), grasp_quat)

# 5. Compute the rigid transformation between the nut hollow center and the grasp pose
T_world_nut = pose_to_matrix(nut_pos, nut_quat)
T_world_grasp = pose_to_matrix(grasp_pos, grasp_quat)
T_nut_grasp = np.linalg.inv(T_world_nut) @ T_world_grasp

# 6. Get the target block pose and determine target end-effector pose for insertion
block_pos, block_quat = get_object_pose('brown square block')
T_world_block = pose_to_matrix(block_pos, block_quat)
T_world_target_ee = T_world_block @ T_nut_grasp
target_pos, target_quat = matrix_to_pose(T_world_target_ee)

# 7. Insert the nut onto the block with vertical approach
goto_pose(target_pos, target_quat, z_approach=0.1)

# 8. Release the nut and retract
open_gripper()
goto_pose(target_pos + np.array([0.0, 0.0, 0.1]), target_quat)