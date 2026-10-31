# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def wxyz_to_xyzw(q):
    return np.array([q[1], q[2], q[3], q[0]])

def xyzw_to_wxyz(q):
    return np.array([q[3], q[0], q[1], q[2]])

def pose_to_matrix(pos, quat_wxyz):
    mat = np.eye(4)
    mat[:3, :3] = R.from_quat(wxyz_to_xyzw(quat_wxyz)).as_matrix()
    mat[:3, 3] = pos
    return mat

def matrix_to_pose(mat):
    pos = mat[:3, 3]
    quat_xyzw = R.from_matrix(mat[:3, :3]).as_quat()
    return pos, xyzw_to_wxyz(quat_xyzw)

# 1. Get the pose of the nut's hollow center and the target peg (brown square block)
nut_center_pos, nut_center_quat = get_object_pose('white hollow center of the brown square nut')
peg_pos, peg_quat = get_object_pose('brown square block')

# 2. Sample a grasp pose on the extruded handle of the brown square nut
grasp_pos, grasp_quat = sample_grasp_pose('extruded handle of the brown square nut')

# 3. Compute the relative transform from the nut center to the grasp pose
# Since the peg insertion primarily requires aligning the XY position (and yaw if needed, or keeping the nut's orientation),
# let's check both full SE(3) relative transform and translational offset.
# Usually in tabletop nut-and-peg tasks (like RoboSuite SquareNut), the peg and nut center frames may have arbitrary relative rotations in detection,
# or the peg is upright and we just translate the nut so its hollow center aligns with the peg's XY position and appropriate Z height.
# Wait: "The nut's object center pose obtained via 'white hollow center of the brown square nut' and the handle grasp pose obtained via 'extruded handle of the brown square nut' have a fixed rigid transform, which must be applied correctly when inserting the nut onto the peg."
T_world_nut = pose_to_matrix(nut_center_pos, nut_center_quat)
T_world_grasp = pose_to_matrix(grasp_pos, grasp_quat)

# Relative transform from nut center to grasp in world frame (or body frame)
# In world frame, if we keep the nut's orientation fixed (or align with peg):
# Wait: does get_object_pose return canonical orientation or bounding-box orientation?
# Notice the prompt says:
# "The nut's object center pose obtained via 'white hollow center of the brown square nut' and the handle grasp pose obtained via 'extruded handle of the brown square nut' have a fixed rigid transform, which must be applied correctly when inserting the nut onto the peg."
# Let's check what happens if we use the offset vector in world frame vs full SE(3).
# Wait: if get_object_pose returns an axis-aligned quaternion (e.g., [1, 0, 0, 0]) for both, then T_world_peg * inv(T_world_nut) * T_world_grasp is identical to translating by (peg_pos - nut_center_pos)!
# What if nut_center_quat and peg_quat are both identity or aligned with the object's symmetry?
# Using T_target_nut = pose_to_matrix(peg_pos, peg_quat), if peg_quat and nut_center_quat are aligned with the square geometry, T_world_peg @ inv(T_world_nut) @ T_world_grasp handles both rotation and translation!
# Wait: what if peg_quat has a Z-flip or different axes? In vision-based get_object_pose, usually object pose is position + identity quaternion (or PCA orientation). Wait—if PCA orientation is used, 'white hollow center of the brown square nut' is a square, and 'brown square block' is a square, or get_object_pose only returns position and identity quaternion [1, 0, 0, 0].
# Even if it returns a quaternion, let's check: if we compute T_nut_to_grasp = np.linalg.inv(T_world_nut) @ T_world_grasp, and target nut pose has position peg_pos (plus a small z offset so it drops onto the peg smoothly) and orientation peg_quat:
# Wait - what if nut_center_quat and peg_quat are NOT identity, or what if they ARE identity?
# Wait: if the nut is already oriented similarly to the peg, or if `get_object_pose` returns [1, 0, 0, 0], both give the exact same result!
# Let's check if we should add a slight Z offset to target_nut_pos so it doesn't collide with the table before dropping, and use z_approach for top-down insertion.

T_nut_to_grasp = np.linalg.inv(T_world_nut) @ T_world_grasp

# Execute grasp
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the nut up first to avoid dragging it across the table or hitting obstacles
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.1
goto_pose(lift_pos, grasp_quat)

# Compute target grasp pose when the nut center is placed at the peg pose
T_world_peg = pose_to_matrix(peg_pos, peg_quat)
T_world_target_grasp = T_world_peg @ T_nut_to_grasp
target_grasp_pos, target_grasp_quat = matrix_to_pose(T_world_target_grasp)

# Ensure a safe clearance height slightly above the peg center height for insertion if needed,
# and use z_approach so the robot moves horizontally above the peg first, then lowers straight down onto the peg.
target_grasp_pos_insert = target_grasp_pos.copy()
target_grasp_pos_insert[2] += 0.02

goto_pose(target_grasp_pos_insert, target_grasp_quat, z_approach=0.1)
open_gripper()

# Retract slightly after releasing
retract_pos = target_grasp_pos_insert.copy()
retract_pos[2] += 0.1
goto_pose(retract_pos, target_grasp_quat)
goto_home_joint_position()