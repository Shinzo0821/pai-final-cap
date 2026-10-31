# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# 1. Open the gripper before approaching
open_gripper()

# 2. Query the grasp pose at the handle and the initial pose of the nut center
grasp_pos, grasp_quat = sample_grasp_pose('extruded handle of the brown square nut')
nut_pos, nut_quat = get_object_pose('white hollow center of the brown square nut')

# 3. Approach and grasp the extruded handle of the nut
goto_pose(grasp_pos, grasp_quat, z_approach=0.05)
close_gripper()

# 4. Lift the nut vertically
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.1])
goto_pose(lift_pos, grasp_quat)

# 5. Get the target pose on the brown square block
block_pos, block_quat = get_object_pose('brown square block')

# Helper functions for 4x4 rigid transformation matrices
# Note: Input quaternion is WXYZ format; scipy uses XYZW format
def pose_to_matrix(pos, quat_wxyz):
    mat = np.eye(4)
    mat[:3, :3] = R.from_quat([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]]).as_matrix()
    mat[:3, 3] = pos
    return mat

def matrix_to_pose(mat):
    pos = mat[:3, 3]
    rot = R.from_matrix(mat[:3, :3])
    q_xyzw = rot.as_quat()
    quat_wxyz = np.array([q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]])
    return pos, quat_wxyz

# Compute the rigid transformation between the nut center and the handle grasp pose:
# T_nut_ee = inv(T_world_nut) @ T_world_grasp
T_world_grasp = pose_to_matrix(grasp_pos, grasp_quat)
T_world_nut = pose_to_matrix(nut_pos, nut_quat)
T_nut_ee = np.linalg.inv(T_world_nut) @ T_world_grasp

# Compute the target end-effector pose when nut center aligns with the block pose:
# T_world_target_ee = T_world_block @ T_nut_ee
T_world_block = pose_to_matrix(block_pos, block_quat)
T_world_target_ee = T_world_block @ T_nut_ee

target_pos, target_quat = matrix_to_pose(T_world_target_ee)

# 6. Insert the nut onto the block with an approach from above
goto_pose(target_pos, target_quat, z_approach=0.08)

# 7. Release the nut and retract
open_gripper()
retract_pos = target_pos + np.array([0.0, 0.0, 0.1])
goto_pose(retract_pos, target_quat)
goto_home_joint_position()