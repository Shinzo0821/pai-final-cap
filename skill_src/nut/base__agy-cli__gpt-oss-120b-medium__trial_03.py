# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# Helper: convert (position, quaternion_wxyz) to homogeneous transformation matrix
def pose_to_matrix(position: np.ndarray, quat_wxyz: np.ndarray) -> np.ndarray:
    # SciPy expects [x, y, z, w]
    quat_xyzw = np.array([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])
    rot = R.from_quat(quat_xyzw).as_matrix()
    mat = np.eye(4)
    mat[:3, :3] = rot
    mat[:3, 3] = position
    return mat

# Helper: convert homogeneous matrix back to (position, quaternion_wxyz)
def matrix_to_pose(mat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    position = mat[:3, 3]
    rot = mat[:3, :3]
    quat_xyzw = R.from_matrix(rot).as_quat()          # [x, y, z, w]
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])
    return position, quat_wxyz

# Return robot to a safe home position and open the gripper
goto_home_joint_position()
open_gripper()

# -------------------------------------------------
# 1. Sample a grasp pose on the handle of the nut
# -------------------------------------------------
handle_pos, handle_quat = sample_grasp_pose('extruded handle of the brown square nut')

# Approach the handle from slightly above (z_approach = 0.05 m)
goto_pose(handle_pos, handle_quat, z_approach=0.05)

# Close the gripper to grasp the nut by its handle
close_gripper()

# -------------------------------------------------
# 2. Compute the pose the handle must have so that
#    the nut's center aligns with the block's insertion point
# -------------------------------------------------
# Get the current world pose of the nut's center
nut_center_pos, nut_center_quat = get_object_pose('white hollow center of the brown square nut')

# Get the world pose of the target block (assumed insertion location)
block_pos, block_quat = get_object_pose('brown square block')

# Build homogeneous matrices
T_handle_world = pose_to_matrix(handle_pos, handle_quat)
T_nut_center_world = pose_to_matrix(nut_center_pos, nut_center_quat)
T_block_world = pose_to_matrix(block_pos, block_quat)

# Fixed transform from handle frame to nut center frame:
T_handle_to_center = np.linalg.inv(T_handle_world) @ T_nut_center_world

# Desired nut center pose = block pose (align center-to-center)
T_target_nut_center_world = T_block_world

# Desired handle pose = target nut center pose transformed back to handle frame
T_target_handle_world = T_target_nut_center_world @ np.linalg.inv(T_handle_to_center)

# Extract position and quaternion for the target handle pose
target_handle_pos, target_handle_quat = matrix_to_pose(T_target_handle_world)

# -------------------------------------------------
# 3. Move to the insertion pose (approach from above, then lower)
# -------------------------------------------------
# First approach a little above the insertion point
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.05)

# Then move straight to the final pose (z_approach = 0.0) to insert the nut
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.0)

# Release the nut onto the block
open_gripper()

# -------------------------------------------------
# 4. Return to a safe home position
# -------------------------------------------------
goto_home_joint_position()