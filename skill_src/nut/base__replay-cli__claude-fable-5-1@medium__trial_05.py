# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# --- Helper: quaternion (wxyz) <-> rotation ---
def quat_to_rot(q_wxyz):
    return R.from_quat([q_wxyz[1], q_wxyz[2], q_wxyz[3], q_wxyz[0]])

def rot_to_quat(r):
    x, y, z, w = r.as_quat()
    return np.array([w, x, y, z])

# --- Perceive nut and peg ---
nut_pos, nut_quat = get_object_pose('white hollow center of the brown square nut')
grasp_pos, grasp_quat = sample_grasp_pose('extruded handle of the brown square nut')
peg_pos, peg_quat = get_object_pose('brown square block')

# Fixed rigid transform between the nut center and the grasp (handle) pose.
# T_nut_to_grasp = T_nut^-1 * T_grasp
R_nut = quat_to_rot(nut_quat)
R_grasp = quat_to_rot(grasp_quat)
R_nut_to_grasp = R_nut.inv() * R_grasp
p_nut_to_grasp = R_nut.inv().apply(grasp_pos - nut_pos)

# --- Grasp the nut by its handle ---
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift straight up
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# --- Compute target nut pose over the peg ---
# Keep the nut's current orientation about vertical axis (same as when grasped) but
# center the nut hole on the peg; align yaw to the peg's yaw.
nut_yaw = R_nut.as_euler('xyz')[2]
peg_yaw = quat_to_rot(peg_quat).as_euler('xyz')[2]
# Choose the smallest yaw rotation that aligns the square nut with the square peg (90 deg symmetry)
dyaw = (peg_yaw - nut_yaw + np.pi / 4) % (np.pi / 2) - np.pi / 4
R_nut_target = R.from_euler('z', dyaw) * R_nut

# Desired nut center position: directly above the peg, then lowered onto it
target_nut_pos = np.array([peg_pos[0], peg_pos[1], nut_pos[2]])

# Grasp (end-effector) pose that produces the target nut pose
R_grasp_target = R_nut_target * R_nut_to_grasp
grasp_target_quat = rot_to_quat(R_grasp_target)
grasp_target_pos = target_nut_pos + R_nut_target.apply(p_nut_to_grasp)

# Hover above the peg, then insert by descending along Z
hover_pos = grasp_target_pos.copy()
hover_pos[2] += 0.15
goto_pose(hover_pos, grasp_target_quat)
goto_pose(grasp_target_pos, grasp_target_quat, z_approach=0.08)

# Release and retreat
open_gripper()
retreat_pos = grasp_target_pos.copy()
retreat_pos[2] += 0.15
goto_pose(retreat_pos, grasp_target_quat)
goto_home_joint_position()