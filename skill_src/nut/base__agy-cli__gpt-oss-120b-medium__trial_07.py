# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def pose_to_matrix(position: np.ndarray, quat_wxyz: np.ndarray) -> np.ndarray:
    """Convert (position, quaternion wxyz) to a 4×4 homogeneous matrix."""
    rot = R.from_quat([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])  # xyzw order for scipy
    mat = np.eye(4)
    mat[:3, :3] = rot.as_matrix()
    mat[:3, 3] = position
    return mat

def matrix_to_pose(mat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert a 4×4 homogeneous matrix to (position, quaternion wxyz)."""
    position = mat[:3, 3]
    rot = R.from_matrix(mat[:3, :3])
    quat_xyzw = rot.as_quat()  # xyzw
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])
    return position, quat_wxyz

# 1. Return to a known safe configuration and open the gripper.
goto_home_joint_position()
open_gripper()

# 2. Get poses.
#   - Grasp pose on the extruded handle of the brown square nut.
handle_pos, handle_quat = sample_grasp_pose("extruded handle of the brown square nut")

#   - Center pose of the nut (white hollow center of the brown square nut).
nut_center_pos, nut_center_quat = get_object_pose("white hollow center of the brown square nut")

#   - Pose of the target block where the nut must be inserted.
block_pos, block_quat = get_object_pose("brown square block")

# 3. Compute the rigid transform from the handle grasp frame to the nut center frame.
T_handle = pose_to_matrix(handle_pos, handle_quat)
T_nut_center = pose_to_matrix(nut_center_pos, nut_center_quat)
T_handle_to_nut = np.linalg.inv(T_handle) @ T_nut_center   # pose of nut center expressed in handle frame

# 4. Compute the desired handle pose that will place the nut center at the block pose.
T_block = pose_to_matrix(block_pos, block_quat)
T_target_handle = T_block @ np.linalg.inv(T_handle_to_nut)

target_handle_pos, target_handle_quat = matrix_to_pose(T_target_handle)

# 5. Move to the handle grasp pose (approach from above) and close the gripper.
goto_pose(handle_pos, handle_quat, z_approach=0.10)   # approach from +Z
goto_pose(handle_pos, handle_quat, z_approach=0.00)   # final grasp pose
close_gripper()

# 6. Move to the insertion pose (approach from above) and release the nut.
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.10)   # approach above the block
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.00)   # insert nut
open_gripper()

# 7. Return to the home joint configuration.
goto_home_joint_position()