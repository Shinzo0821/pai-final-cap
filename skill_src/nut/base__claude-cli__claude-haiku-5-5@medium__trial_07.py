# Code block 0
# Grasp the nut by its handle, then insert it onto the block.
# The handle grasp and the nut center have a fixed rigid transform T_rel = inv(T_grasp) @ T_center,
# so the grasp target is T_grasp_target = T_center_target @ inv(T_rel).

import numpy as np
from scipy.spatial.transform import Rotation as R


def pose_to_mat(position, quat_wxyz):
    # Convert position + WXYZ quaternion into a 4x4 homogeneous transform.
    q = np.asarray(quat_wxyz, dtype=float)
    T = np.eye(4)
    T[:3, :3] = R.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()  # scipy expects XYZW
    T[:3, 3] = np.asarray(position, dtype=float)
    return T


def mat_to_pose(T):
    # Convert a 4x4 transform back into (position, WXYZ quaternion).
    q_xyzw = R.from_matrix(T[:3, :3]).as_quat()
    position = T[:3, 3].copy()
    quat_wxyz = np.array([q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]])
    return position, quat_wxyz


# 1. Start from a known state with the gripper open.
open_gripper()

# 2. Sample a grasp pose on the extruded handle of the nut.
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")

# 3. Get the nut center pose and compute the fixed transform from grasp frame to nut center.
center_pos, center_quat = get_object_pose("white hollow center of the brown square nut")
T_grasp = pose_to_mat(grasp_pos, grasp_quat)
T_center = pose_to_mat(center_pos, center_quat)
T_rel = np.linalg.inv(T_grasp) @ T_center  # nut center expressed in the grasp frame

# 4. Approach the handle from above and grasp.
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# 5. Lift the nut clear of the table.
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.1])
goto_pose(lift_pos, grasp_quat)

# 6. Compute the target nut center pose above the peg of the brown square block.
#    Orientation is taken from the block so the square nut aligns with the block.
block_pos, block_quat = get_object_pose("brown square block")
T_block = pose_to_mat(block_pos, block_quat)
T_center_target = T_block.copy()
T_center_target[:3, 3] += np.array([0.0, 0.0, 0.05])  # hover 5 cm above the block for insertion

# 7. Convert the nut center target back into a grasp (end-effector) target.
T_grasp_target = T_center_target @ np.linalg.inv(T_rel)
target_pos, target_quat = mat_to_pose(T_grasp_target)

# 8. Move above the peg, then lower onto it.
goto_pose(target_pos, target_quat, z_approach=0.05)

# 9. Release the nut on the block.
open_gripper()

# 10. Retract upward and return home.
retract_pos = target_pos + np.array([0.0, 0.0, 0.1])
goto_pose(retract_pos, target_quat)
goto_home_joint_position()