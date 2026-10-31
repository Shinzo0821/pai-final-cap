# Code block 0
import numpy as np


def quat_mul(q1, q2):
    # Hamilton product for WXYZ quaternions
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ])


def quat_conj(q):
    # Inverse of a unit quaternion
    return np.array([q[0], -q[1], -q[2], -q[3]])


def quat_normalize(q):
    q = np.asarray(q, dtype=float)
    return q / np.linalg.norm(q)


def quat_rotate(q, v):
    # Rotate 3D vector v by unit quaternion q
    p = np.array([0.0, v[0], v[1], v[2]])
    return quat_mul(quat_mul(q, p), quat_conj(q))[1:]


# 1) Open gripper before approaching
open_gripper()

# 2) Grasp pose on the handle of the nut
handle_pos, handle_quat = sample_grasp_pose("extruded handle of the brown square nut")
handle_quat = quat_normalize(handle_quat)

# 3) Nut object-center pose (white hollow center) at the initial configuration
nut_pos, nut_quat = get_object_pose("white hollow center of the brown square nut")
nut_quat = quat_normalize(nut_quat)

# 4) Fixed rigid transform from nut center to handle grasp, expressed in the nut frame
#    rel_pos = R_nut^T (p_handle - p_nut), rel_quat = q_nut^-1 * q_handle
rel_pos = quat_rotate(quat_conj(nut_quat), handle_pos - nut_pos)
rel_quat = quat_normalize(quat_mul(quat_conj(nut_quat), handle_quat))

# 5) Approach the handle from above, close the gripper
goto_pose(handle_pos, handle_quat, z_approach=0.1)
close_gripper()

# 6) Lift the nut clear of the table
lift_pos = handle_pos + np.array([0.0, 0.0, 0.1])
goto_pose(lift_pos, handle_quat)

# 7) Target: brown square block (peg). Align nut center with block pose.
block_pos, block_quat = get_object_pose("brown square block")
block_quat = quat_normalize(block_quat)

# Desired nut-center pose: hover above the peg, then lower onto it
hover_nut_pos = block_pos + np.array([0.0, 0.0, 0.08])
insert_nut_pos = block_pos + np.array([0.0, 0.0, 0.02])
target_nut_quat = block_quat

# Convert desired nut-center poses to end-effector (handle) poses using the fixed transform
#   p_handle = p_nut + R_nut * rel_pos
#   q_handle = q_nut * rel_quat
hover_handle_pos = hover_nut_pos + quat_rotate(target_nut_quat, rel_pos)
insert_handle_pos = insert_nut_pos + quat_rotate(target_nut_quat, rel_pos)
target_handle_quat = quat_normalize(quat_mul(target_nut_quat, rel_quat))

# 8) Move above the peg, then insert
goto_pose(hover_handle_pos, target_handle_quat)
goto_pose(insert_handle_pos, target_handle_quat)

# 9) Release the nut and retreat
open_gripper()
retreat_pos = insert_handle_pos + np.array([0.0, 0.0, 0.1])
goto_pose(retreat_pos, target_handle_quat)

# 10) Return to home configuration
goto_home_joint_position()