# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def wxyz_to_rot(q):
    return R.from_quat([q[1], q[2], q[3], q[0]])

def rot_to_wxyz(r):
    x, y, z, w = r.as_quat()
    return np.array([w, x, y, z])

def yaw_of(r):
    x_axis = r.apply([1.0, 0.0, 0.0])
    return np.arctan2(x_axis[1], x_axis[0])

# Get the poses of the nut, its handle grasp, and the block
nut_pos, nut_quat = get_object_pose("white hollow center of the brown square nut")
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")
block_pos, block_quat = get_object_pose("brown square block")

R_nut = wxyz_to_rot(nut_quat)
R_grasp = wxyz_to_rot(grasp_quat)
R_block = wxyz_to_rot(block_quat)

# Fixed rigid transform from the nut center to the handle grasp, in the nut frame
R_nut_grasp = R_nut.inv() * R_grasp
p_nut_grasp = R_nut.inv().apply(grasp_pos - nut_pos)

# Grasp the handle
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the nut
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.2])
goto_pose(lift_pos, grasp_quat)

# Target nut orientation: rotate by the smallest yaw that aligns the square nut with the square block
# (square symmetry, so wrap to [-pi/4, pi/4])
delta = yaw_of(R_block) - yaw_of(R_nut)
delta = (delta + np.pi / 4) % (np.pi / 2) - np.pi / 4
R_nut_target = R.from_euler("z", delta) * R_nut

# Target nut center: above the peg in xy, at roughly its original resting height in z
nut_target_pos = np.array([block_pos[0], block_pos[1], nut_pos[2] + 0.01])

# Apply the rigid transform to get the end-effector target pose
R_grasp_target = R_nut_target * R_nut_grasp
grasp_target_pos = nut_target_pos + R_nut_target.apply(p_nut_grasp)
grasp_target_quat = rot_to_wxyz(R_grasp_target)

# Move above the peg first, then lower the nut onto it
above_pos = grasp_target_pos + np.array([0.0, 0.0, 0.2])
goto_pose(above_pos, grasp_target_quat)
goto_pose(grasp_target_pos, grasp_target_quat, z_approach=0.15)

# Release the nut and retreat
open_gripper()
goto_pose(grasp_target_pos + np.array([0.0, 0.0, 0.15]), grasp_target_quat)
goto_home_joint_position()