# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# Helper to convert position and wxyz quaternion to 4x4 transformation matrix
def pose_to_matrix(position, quat_wxyz):
    T = np.eye(4)
    T[:3, :3] = R.from_quat([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]]).as_matrix()
    T[:3, 3] = position
    return T

# Helper to convert 4x4 transformation matrix to position and wxyz quaternion
def matrix_to_pose(T):
    position = T[:3, 3]
    xyzw = R.from_matrix(T[:3, :3]).as_quat()
    quat_wxyz = np.array([xyzw[3], xyzw[0], xyzw[1], xyzw[2]])
    return position, quat_wxyz

# 1. Open the gripper before approaching
open_gripper()

# 2. Get initial poses of the nut center, the handle grasp pose, and the target block
nut_pos, nut_quat_wxyz = get_object_pose('white hollow center of the brown square nut')
grasp_pos, grasp_quat_wxyz = sample_grasp_pose('extruded handle of the brown square nut')
block_pos, block_quat_wxyz = get_object_pose('brown square block')

# 3. Compute rigid transform from nut center to grasp pose
T_world_nut = pose_to_matrix(nut_pos, nut_quat_wxyz)
T_world_grasp = pose_to_matrix(grasp_pos, grasp_quat_wxyz)
T_nut_grasp = np.linalg.inv(T_world_nut) @ T_world_grasp

# 4. Move to grasp pose with approach offset along z-axis, then close gripper
goto_pose(grasp_pos, grasp_quat_wxyz, z_approach=0.05)
close_gripper()

# 5. Lift the nut up after grasping
goto_pose(grasp_pos + np.array([0.0, 0.0, 0.1]), grasp_quat_wxyz)

# 6. Compute target end-effector pose for inserting onto the brown square block
T_world_block = pose_to_matrix(block_pos, block_quat_wxyz)
T_world_target_ee = T_world_block @ T_nut_grasp
target_pos, target_quat_wxyz = matrix_to_pose(T_world_target_ee)

# 7. Insert the nut onto the block with z approach motion
goto_pose(target_pos, target_quat_wxyz, z_approach=0.05)

# 8. Release the nut and retreat
open_gripper()
goto_pose(target_pos + np.array([0.0, 0.0, 0.1]), target_quat_wxyz)