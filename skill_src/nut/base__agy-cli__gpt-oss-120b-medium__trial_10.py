# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# 1. Get the pose of the nut's center (reference for insertion)
nut_center_pos, nut_center_quat = get_object_pose("white hollow center of the brown square nut")
# 2. Sample a grasp pose on the extruded handle of the nut
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")

# Helper to build a 4x4 homogeneous transformation matrix from position + quaternion (WXYZ)
def pose_to_homogeneous(pos, quat_wxyz):
    rot = R.from_quat([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])  # convert to XYZW
    T = np.eye(4)
    T[:3, :3] = rot.as_matrix()
    T[:3, 3] = pos
    return T

# Helper to decompose a homogeneous matrix back to position + quaternion (WXYZ)
def homogeneous_to_pose(T):
    rot = R.from_matrix(T[:3, :3])
    quat_xyzw = rot.as_quat()  # XYZW
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])  # WXYZ
    pos = T[:3, 3]
    return pos, quat_wxyz

# 3. Compute the rigid transform from the grasp pose (handle) to the nut center
T_handle = pose_to_homogeneous(grasp_pos, grasp_quat)
T_center = pose_to_homogeneous(nut_center_pos, nut_center_quat)
T_offset = np.linalg.inv(T_handle) @ T_center  # transforms a point expressed in handle frame to nut-center frame

# 4. Move to the grasp pose and close the gripper
goto_pose(grasp_pos, grasp_quat, z_approach=0.05)  # approach from above
close_gripper()

# 5. Get the pose of the target block where the nut will be inserted
block_pos, block_quat = get_object_pose("brown square block")
T_block = pose_to_homogeneous(block_pos, block_quat)

# 6. Compute the desired gripper pose (handle pose) such that the nut center aligns with the block pose
# Desired handle pose = inverse(T_offset) * block_pose
T_target_handle = np.linalg.inv(T_offset) @ T_block
target_pos, target_quat = homogeneous_to_pose(T_target_handle)

# 7. Move to the insertion pose (approach from above)
goto_pose(target_pos, target_quat, z_approach=0.05)  # approach from above the block
open_gripper()  # release the nut onto the block

# 8. Return home
goto_home_joint_position()