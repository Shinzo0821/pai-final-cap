# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def wxyz_to_xyzw(q):
    return np.array([q[1], q[2], q[3], q[0]])

def xyzw_to_wxyz(q):
    return np.array([q[3], q[0], q[1], q[2]])

# 1. Open gripper before approaching the object
open_gripper()

# 2. Get the necessary poses
# Object center pose of the nut
nut_pos, nut_quat_wxyz = get_object_pose('white hollow center of the brown square nut')

# Grasp pose at the handle
grasp_pos, grasp_quat_wxyz = sample_grasp_pose('extruded handle of the brown square nut')

# Pose of the target square block
block_pos, block_quat_wxyz = get_object_pose('brown square block')

# 3. Move to grasp pose with approach offset, then grasp
goto_pose(grasp_pos, grasp_quat_wxyz, z_approach=0.08)
close_gripper()

# 4. Lift the nut up
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.15])
goto_pose(lift_pos, grasp_quat_wxyz)

# 5. Compute the relative transform between the nut center and the handle grasp pose
r_nut = R.from_quat(wxyz_to_xyzw(nut_quat_wxyz))
r_grasp = R.from_quat(wxyz_to_xyzw(grasp_quat_wxyz))
r_block = R.from_quat(wxyz_to_xyzw(block_quat_wxyz))

# Transform from nut center frame to grasp pose frame:
# T_nut_to_grasp = T_nut^{-1} * T_grasp
r_nut_to_grasp = r_nut.inv() * r_grasp
p_nut_to_grasp = r_nut.inv().apply(grasp_pos - nut_pos)

# Compute target end-effector pose when nut center aligns with block pose
r_target = r_block * r_nut_to_grasp
p_target = block_pos + r_block.apply(p_nut_to_grasp)
target_quat_wxyz = xyzw_to_wxyz(r_target.as_quat())

# 6. Insert the nut onto the block with approach from above
goto_pose(p_target, target_quat_wxyz, z_approach=0.10)

# 7. Release the nut and retract arm
open_gripper()
goto_pose(p_target + np.array([0.0, 0.0, 0.10]), target_quat_wxyz)
goto_home_joint_position()