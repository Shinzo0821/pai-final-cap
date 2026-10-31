# Code block 0
import numpy as np

# ---------- small pose helpers (numpy only) ----------

def quat_wxyz_to_mat(q):
    q = np.asarray(q, dtype=float)
    q = q / np.linalg.norm(q)
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def mat_to_quat_wxyz(R):
    tr = np.trace(R)
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    q = np.array([w, x, y, z], dtype=float)
    return q / np.linalg.norm(q)


def pose_to_mat(position, quaternion_wxyz):
    T = np.eye(4)
    T[:3, :3] = quat_wxyz_to_mat(quaternion_wxyz)
    T[:3, 3] = np.asarray(position, dtype=float)
    return T


def mat_to_pose(T):
    return T[:3, 3].copy(), mat_to_quat_wxyz(T[:3, :3])


def inv_T(T):
    Ti = np.eye(4)
    Ti[:3, :3] = T[:3, :3].T
    Ti[:3, 3] = -T[:3, :3].T @ T[:3, 3]
    return Ti


# ---------- 1. Estimate grasp pose on the nut handle ----------

# Grasp pose (end-effector) on the extruded handle, world frame
grasp_p, grasp_q = sample_grasp_pose("extruded handle of the brown square nut")
T_ee_grasp = pose_to_mat(grasp_p, grasp_q)

# Nut object-center pose (white hollow center), world frame
center_p, center_q = get_object_pose("white hollow center of the brown square nut")
T_center = pose_to_mat(center_p, center_q)

# Fixed rigid transform: nut center expressed in the end-effector frame.
# Once grasped, the nut moves with the end-effector, so this stays constant.
T_ee_to_center = inv_T(T_ee_grasp) @ T_center

# ---------- 2. Grasp the nut by its handle ----------

open_gripper()
goto_pose(grasp_p, grasp_q, z_approach=0.10)
close_gripper()

# Lift the nut straight up before moving toward the peg
lift_p = grasp_p.copy()
lift_p[2] += 0.10
goto_pose(lift_p, grasp_q)

# ---------- 3. Compute target placement on the brown square block ----------

block_p, block_q = get_object_pose("brown square block")
T_block = pose_to_mat(block_p, block_q)

# Desired nut-center pose: aligned with block orientation, centered over the peg.
# Small height offset so the hollow center sits just above the peg top.
T_target_center = T_block.copy()
T_target_center[2, 3] += 0.02

# End-effector pose that places the nut center at the target:
# T_center_target = T_ee_target @ T_ee_to_center  =>  T_ee_target = T_center_target @ inv(T_ee_to_center)
T_ee_target = T_target_center @ inv_T(T_ee_to_center)
target_p, target_q = mat_to_pose(T_ee_target)

# ---------- 4. Insert the nut onto the peg ----------

# Approach from above, then descend onto the peg
goto_pose(target_p, target_q, z_approach=0.05)

# Release the nut
open_gripper()

# ---------- 5. Retreat and return home ----------

retreat_p = target_p.copy()
retreat_p[2] += 0.10
goto_pose(retreat_p, target_q)
goto_home_joint_position()