# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def pose_to_matrix(position: np.ndarray, quat_wxyz: np.ndarray) -> np.ndarray:
    """Convert position (3,) and quaternion (WXYZ) to a 4x4 homogeneous matrix."""
    rot = R.from_quat([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])  # xyzw order
    mat = np.eye(4)
    mat[:3, :3] = rot.as_matrix()
    mat[:3, 3] = position
    return mat

def matrix_to_pose(mat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert 4x4 homogeneous matrix back to position (3,) and quaternion (WXYZ)."""
    position = mat[:3, 3]
    rot = R.from_matrix(mat[:3, :3])
    quat_xyzw = rot.as_quat()  # xyzw
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])
    return position, quat_wxyz

# 1. Return to a safe home configuration
goto_home_joint_position()

# 2. Open the gripper ready to grasp
open_gripper()

# 3. Obtain a grasp pose on the extruded handle of the nut
handle_pos, handle_quat = sample_grasp_pose('extruded handle of the brown square nut')

# 4. Approach the handle from above (10 cm offset in Z)
goto_pose(handle_pos, handle_quat, z_approach=0.10)

# 5. Close the gripper to secure the nut by its handle
close_gripper()

# 6. Lift the nut slightly after grasping
goto_pose(handle_pos, handle_quat, z_approach=0.10)

# 7. Compute the rigid transform from the handle grasp pose to the nut's center
nut_center_pos, nut_center_quat = get_object_pose('white hollow center of the brown square nut')
T_handle = pose_to_matrix(handle_pos, handle_quat)
T_nut = pose_to_matrix(nut_center_pos, nut_center_quat)
T_handle_to_nut = np.linalg.inv(T_handle) @ T_nut  # Transform from handle frame to nut center frame
T_nut_to_handle = np.linalg.inv(T_handle_to_nut)

# 8. Get the pose of the target block where the nut should be inserted
block_pos, block_quat = get_object_pose('brown square block')
T_block = pose_to_matrix(block_pos, block_quat)

# 9. Determine the desired handle pose that will place the nut's center at the block pose
T_target_handle = T_block @ T_nut_to_handle
target_handle_pos, target_handle_quat = matrix_to_pose(T_target_handle)

# 10. Move above the insertion point (10 cm offset)
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.10)

# 11. Perform the insertion by moving to the exact target pose
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.0)

# 12. Release the nut onto the block
open_gripper()

# 13. Retract the arm upward
goto_pose(target_handle_pos, target_handle_quat, z_approach=0.10)

# 14. Return to the home configuration
goto_home_joint_position()