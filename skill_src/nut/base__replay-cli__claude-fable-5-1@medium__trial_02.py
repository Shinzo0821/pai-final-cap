# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

# --- Perceive ---
nut_center_pos, nut_center_quat = get_object_pose("white hollow center of the brown square nut")
peg_pos, peg_quat = get_object_pose("brown square block")
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")

def quat_to_rot(q_wxyz):
    return R.from_quat([q_wxyz[1], q_wxyz[2], q_wxyz[3], q_wxyz[0]])

def rot_to_quat(r):
    q = r.as_quat()  # xyzw
    return np.array([q[3], q[0], q[1], q[2]])

# Fixed rigid transform from nut center to grasp (handle) pose, expressed in the nut center frame
R_nut = quat_to_rot(nut_center_quat)
R_grasp = quat_to_rot(grasp_quat)
t_nut_to_grasp = R_nut.inv().apply(grasp_pos - nut_center_pos)
R_nut_to_grasp = R_nut.inv() * R_grasp

# --- Grasp the handle ---
goto_home_joint_position()
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift straight up
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# --- Compute target nut-center pose above the peg ---
# Keep the nut's current orientation about roll/pitch, but align yaw with the peg (square peg).
R_peg = quat_to_rot(peg_quat)
peg_yaw = R_peg.as_euler("xyz")[2]
nut_rpy = R_nut.as_euler("xyz")
# Square nut has 90 deg symmetry: pick the yaw closest to current nut yaw
candidate_yaws = [peg_yaw + k * np.pi / 2 for k in range(4)]
nut_yaw = nut_rpy[2]
best_yaw = min(candidate_yaws, key=lambda y: abs((y - nut_yaw + np.pi) % (2 * np.pi) - np.pi))
R_nut_target = R.from_euler("xyz", [nut_rpy[0], nut_rpy[1], best_yaw])

# Target nut center: directly above peg, then lowered onto it
target_nut_pos_high = peg_pos.copy()
target_nut_pos_high[2] = peg_pos[2] + 0.12
target_nut_pos_low = peg_pos.copy()
target_nut_pos_low[2] = peg_pos[2] + 0.005

# Convert nut-center target to end-effector target using the fixed rigid transform
def ee_from_nut(nut_pos, R_nut_t):
    ee_pos = nut_pos + R_nut_t.apply(t_nut_to_grasp)
    ee_rot = R_nut_t * R_nut_to_grasp
    return ee_pos, rot_to_quat(ee_rot)

ee_high_pos, ee_high_quat = ee_from_nut(target_nut_pos_high, R_nut_target)
ee_low_pos, ee_low_quat = ee_from_nut(target_nut_pos_low, R_nut_target)

# --- Move above peg and insert ---
goto_pose(ee_high_pos, ee_high_quat)
goto_pose(ee_low_pos, ee_low_quat, z_approach=0.05)

# Release and retreat
open_gripper()
retreat_pos = ee_low_pos.copy()
retreat_pos[2] += 0.15
goto_pose(retreat_pos, ee_low_quat)
goto_home_joint_position()