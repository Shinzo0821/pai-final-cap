# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# Helper: (position, quaternion_wxyz) -> 4x4 homogeneous transform
def pose_to_mat(pos, quat_wxyz):
    q = np.asarray(quat_wxyz, dtype=float)
    T = np.eye(4)
    # scipy expects xyzw ordering
    T[:3, :3] = R.from_quat([q[1], q[2], q[3], q[0]]).as_matrix()
    T[:3, 3] = np.asarray(pos, dtype=float)
    return T

# Helper: 4x4 homogeneous transform -> (position, quaternion_wxyz)
def mat_to_pose(T):
    q_xyzw = R.from_matrix(T[:3, :3]).as_quat()
    quat_wxyz = np.array([q_xyzw[3], q_xyzw[0], q_xyzw[1], q_xyzw[2]])
    return T[:3, 3].copy(), quat_wxyz

# 1) Move to a safe home configuration with the gripper open
open_gripper()
goto_home_joint_position()

# 2) Get the handle grasp pose (end-effector pose in world frame)
grasp_pos, grasp_quat = sample_grasp_pose('extruded handle of the brown square nut')

# 3) Get the nut's object center pose, then compute the fixed rigid transform
#    between the nut center and the end-effector grasp pose (expressed in nut frame).
nut_center_pos, nut_center_quat = get_object_pose('white hollow center of the brown square nut')
T_w_grasp = pose_to_mat(grasp_pos, grasp_quat)
T_w_nut = pose_to_mat(nut_center_pos, nut_center_quat)
T_nut_ee = np.linalg.inv(T_w_nut) @ T_w_grasp  # fixed EE pose relative to nut center

# 4) Approach the handle, grasp it, and lift
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

lift_pos = grasp_pos + np.array([0.0, 0.0, 0.10])
goto_pose(lift_pos, grasp_quat)

# 5) Find the target peg (brown square block) and compute the desired nut center pose.
#    The nut's orientation is matched to the block's orientation.
block_pos, block_quat = get_object_pose('brown square block')

# Desired nut center: directly above the peg for approach, then lowered onto it.
# Height offsets are heuristic and may need tuning for the scene.
insert_center_pos = block_pos + np.array([0.0, 0.0, 0.05])
T_w_nut_target = pose_to_mat(insert_center_pos, block_quat)

# 6) Convert the desired nut center pose into an end-effector target pose
#    using the fixed nut-to-EE transform recorded above.
T_w_ee_target = T_w_nut_target @ T_nut_ee
ee_target_pos, ee_target_quat = mat_to_pose(T_w_ee_target)

# 7) Move above the peg, then descend and insert
goto_pose(ee_target_pos, ee_target_quat, z_approach=0.08)

# Lower slightly to seat the nut onto the peg
T_w_nut_seat = pose_to_mat(block_pos + np.array([0.0, 0.0, 0.01]), block_quat)
T_w_ee_seat = T_w_nut_seat @ T_nut_ee
seat_pos, seat_quat = mat_to_pose(T_w_ee_seat)
goto_pose(seat_pos, seat_quat)

# 8) Release the nut and retreat
open_gripper()

retreat_pos = seat_pos + np.array([0.0, 0.0, 0.10])
goto_pose(retreat_pos, seat_quat)
goto_home_joint_position()