# Code block 0
# Grasp the nut by its handle, then insert it onto the peg using the fixed handle-to-nut transform.
import numpy as np
from scipy.spatial.transform import Rotation as R

def to_mat(p, q_wxyz):
    # Convert (position, WXYZ quaternion) to a 4x4 homogeneous transform.
    q = np.asarray(q_wxyz, dtype=float)
    T = np.eye(4)
    T[:3, :3] = R.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()  # scipy expects XYZW
    T[:3, 3] = np.asarray(p, dtype=float)
    return T

def from_mat(T):
    # Convert a 4x4 transform back to (position, WXYZ quaternion).
    xyzw = R.from_matrix(T[:3, :3]).as_quat()
    wxyz = np.array([xyzw[3], xyzw[0], xyzw[1], xyzw[2]])
    return T[:3, 3].copy(), wxyz

# Start from a known configuration with the gripper open.
goto_home_joint_position()
open_gripper()

# Grasp pose on the handle. Use the quaternion returned by sample_grasp_pose.
handle_p, handle_q = sample_grasp_pose("extruded handle of the brown square nut")

# Nut center pose, used to compute the fixed rigid transform between nut center and handle grasp.
nut_center_p, nut_center_q = get_object_pose("white hollow center of the brown square nut")

T_world_grasp = to_mat(handle_p, handle_q)
T_world_nut = to_mat(nut_center_p, nut_center_q)

# Fixed transform: grasp pose expressed in the nut's frame. Constant as long as the nut is rigidly held.
T_nut_grasp = np.linalg.inv(T_world_nut) @ T_world_grasp

# Approach the handle from above, grasp, and lift.
goto_pose(handle_p, handle_q, z_approach=0.1)
close_gripper()

lift_p = handle_p + np.array([0.0, 0.0, 0.1])
goto_pose(lift_p, handle_q)

# Peg (brown square block) pose.
peg_p, peg_q = get_object_pose("brown square block")

# Target nut center: aligned with the peg, slightly above it for a safe pre-insertion.
target_nut_p = peg_p + np.array([0.0, 0.0, 0.05])
T_world_target_nut = to_mat(target_nut_p, peg_q)

# Apply the fixed nut-to-grasp transform to get the gripper target pose.
T_world_target_grasp = T_world_target_nut @ T_nut_grasp
target_grasp_p, target_grasp_q = from_mat(T_world_target_grasp)

# Move above the peg, then lower into the insertion pose.
pre_insert_p = target_grasp_p + np.array([0.0, 0.0, 0.05])
goto_pose(pre_insert_p, target_grasp_q)
goto_pose(target_grasp_p, target_grasp_q)

# Release the nut on the peg and retreat.
open_gripper()
retreat_p = target_grasp_p + np.array([0.0, 0.0, 0.1])
goto_pose(retreat_p, target_grasp_q)
goto_home_joint_position()