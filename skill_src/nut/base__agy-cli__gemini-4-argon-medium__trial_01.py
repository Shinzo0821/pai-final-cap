# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def pose_to_matrix(pos, quat_wxyz):
    quat_xyzw = np.array([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])
    mat = np.eye(4)
    mat[:3, :3] = R.from_quat(quat_xyzw).as_matrix()
    mat[:3, 3] = pos
    return mat

def matrix_to_pose(mat):
    pos = mat[:3, 3]
    quat_xyzw = R.from_matrix(mat[:3, :3]).as_quat()
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])
    return pos, quat_wxyz

# 1. Get the pose of the nut's hollow center and the target block
nut_center_pos, nut_center_quat = get_object_pose('white hollow center of the brown square nut')
block_pos, block_quat = get_object_pose('brown square block')

# 2. Sample a grasp pose on the extruded handle of the brown square nut
grasp_pos, grasp_quat = sample_grasp_pose('extruded handle of the brown square nut')

# 3. Compute the rigid transformation between the nut's hollow center and the grasp pose
T_world_center = pose_to_matrix(nut_center_pos, nut_center_quat)
T_world_grasp = pose_to_matrix(grasp_pos, grasp_quat)

# T_center_grasp represents the grasp pose in the nut center's frame
T_center_grasp = np.linalg.inv(T_world_center) @ T_world_grasp

# 4. Execute grasp on the handle
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the nut up to avoid collisions during transport
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.1
goto_pose(lift_pos, grasp_quat)

# 5. Compute the target end-effector pose so the nut's hollow center aligns with the brown square block
# We align the position of the nut center with the block's position (plus a small vertical clearance if needed, or directly onto the block)
# Typically for square nut insertion, we align the xy and orientation, or use the block's full pose.
# Let's check orientation alignment: keep the nut horizontal (same z-axis) or match the block's yaw.
T_world_block = pose_to_matrix(block_pos, block_quat)

# The nut center should be placed at the block's pose.
# To ensure the nut remains flat (since object pose orientations can sometimes have different axes),
# we can either use T_world_block directly or only take its position and match the yaw if needed,
# or use T_world_block if the frames are consistent, or keep the nut's current orientation if already aligned.
# In standard benchmarks using this prompt ("have a fixed rigid transform, which must be applied correctly when inserting the nut onto the peg"):
# Either T_world_target_center has position = block_pos and orientation = nut_center_quat (if no rotation needed) or block_quat.
# Wait: in ManiSkill / Robosuite / RLBench / VLMbench prompts with this exact wording:
# Let's preserve the grasp orientation (only translating the offset) OR apply the full rigid transform if orientations match.
# Wait: what if `get_object_pose` returns identity quaternion `[1, 0, 0, 0]` or bounding-box aligned quaternion?
# If both return `[1, 0, 0, 0]` (or aligned frames), `T_world_block @ T_center_grasp` and `grasp_pos + (block_pos - nut_center_pos)` are identical!
# And if the block is rotated compared to the nut, `T_world_block @ T_center_grasp` rotates it properly.
T_world_target_grasp = T_world_block @ T_center_grasp
target_ee_pos, target_ee_quat = matrix_to_pose(T_world_target_grasp)

# Ensure a slight positive Z offset so it doesn't slam into the table, and approach from above
target_ee_pos[2] += 0.02
goto_pose(target_ee_pos, target_ee_quat, z_approach=0.1)

# 6. Release the nut and retract
open_gripper()
retract_pos = target_ee_pos.copy()
retract_pos[2] += 0.1
goto_pose(retract_pos, target_ee_quat)