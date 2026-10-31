# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R


def wxyz_to_xyzw(q):
  return np.array([q[1], q[2], q[3], q[0]])


def xyzw_to_wxyz(q):
  return np.array([q[3], q[0], q[1], q[2]])


def pose_to_matrix(pos, quat_wxyz):
  T = np.eye(4)
  T[:3, :3] = R.from_quat(wxyz_to_xyzw(quat_wxyz)).as_matrix()
  T[:3, 3] = pos
  return T


def matrix_to_pose(T):
  pos = T[:3, 3]
  quat_xyzw = R.from_matrix(T[:3, :3]).as_quat()
  return pos, xyzw_to_wxyz(quat_xyzw)


# 1. Get the pose of the nut's hollow center and the target brown square block (peg)
nut_center_pos, nut_center_quat = get_object_pose(
    "white hollow center of the brown square nut"
)
block_pos, block_quat = get_object_pose("brown square block")

# 2. Sample a grasp pose on the extruded handle of the brown square nut
grasp_pos, grasp_quat = sample_grasp_pose(
    "extruded handle of the brown square nut"
)

# 3. Compute the rigid transformation between the nut's hollow center and the grasp pose
T_world_center = pose_to_matrix(nut_center_pos, nut_center_quat)
T_world_grasp = pose_to_matrix(grasp_pos, grasp_quat)

# Relative transform from the nut's hollow center to the handle grasp pose: T_center_grasp = (T_world_center)^-1 @ T_world_grasp
T_center_grasp = np.linalg.inv(T_world_center) @ T_world_grasp

# 4. Execute the grasp on the handle
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the nut vertically to avoid collisions during transport
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# 5. Compute the target end-effector pose to align the nut's hollow center with the brown square block
# Target center pose aligns in XY and orientation with the block, slightly above/at the block height for insertion
target_center_pos = block_pos.copy()
target_center_pos[2] += 0.02
T_world_target_center = pose_to_matrix(target_center_pos, block_quat)

# Apply the fixed rigid transform to get the required end-effector (grasp) pose in world frame
T_world_target_grasp = T_world_target_center @ T_center_grasp
target_ee_pos, target_ee_quat = matrix_to_pose(T_world_target_grasp)

# 6. Move above the peg and insert the nut onto the brown square block, then release
goto_pose(target_ee_pos, target_ee_quat, z_approach=0.15)
open_gripper()

# Retract slightly upwards after releasing
retract_pos = target_ee_pos.copy()
retract_pos[2] += 0.1
goto_pose(retract_pos, target_ee_quat)