# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# 1. Open the gripper to prepare for grasping
open_gripper()

# 2. Get the handle grasp pose and the nut's hollow center pose
grasp_pos, grasp_quat_wxyz = sample_grasp_pose('extruded handle of the brown square nut')
nut_pos, nut_quat_wxyz = get_object_pose('white hollow center of the brown square nut')

# 3. Approach and grasp the handle
goto_pose(grasp_pos, grasp_quat_wxyz, z_approach=0.08)
close_gripper()

# 4. Lift the nut up after grasping
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat_wxyz)

# 5. Get the pose of the brown square block
block_pos, block_quat_wxyz = get_object_pose('brown square block')

# 6. Compute transformation matrices to solve for the target end-effector pose
def pose_to_matrix(pos, quat_wxyz):
    T = np.eye(4)
    # Scipy expects quaternion in [x, y, z, w] format
    rot = R.from_quat([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])
    T[:3, :3] = rot.as_matrix()
    T[:3, 3] = pos
    return T

def matrix_to_pose(T):
    pos = T[:3, 3]
    rot = R.from_matrix(T[:3, :3])
    q = rot.as_quat()  # [x, y, z, w]
    quat_wxyz = np.array([q[3], q[0], q[1], q[2]])
    return pos, quat_wxyz

T_world_nut = pose_to_matrix(nut_pos, nut_quat_wxyz)
T_world_grasp = pose_to_matrix(grasp_pos, grasp_quat_wxyz)

# Relative transform from the nut center to the end-effector grasp pose
T_nut_ee = np.linalg.inv(T_world_nut) @ T_world_grasp

# Desired end-effector pose when nut center is at the block pose
T_world_block = pose_to_matrix(block_pos, block_quat_wxyz)
T_world_insert = T_world_block @ T_nut_ee

insert_pos, insert_quat_wxyz = matrix_to_pose(T_world_insert)

# 7. Insert the nut onto the block using z_approach for a smooth vertical downward motion
goto_pose(insert_pos, insert_quat_wxyz, z_approach=0.1)

# 8. Release the nut and reset the arm configuration
open_gripper()
goto_home_joint_position()