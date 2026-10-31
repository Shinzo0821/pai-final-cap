# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation as R

def pose_to_matrix(pos, quat_wxyz):
    quat_xyzw = np.array([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])
    rot = R.from_quat(quat_xyzw).as_matrix()
    mat = np.eye(4)
    mat[:3, :3] = rot
    mat[:3, 3] = pos
    return mat

def matrix_to_pose(mat):
    pos = mat[:3, 3]
    quat_xyzw = R.from_matrix(mat[:3, :3]).as_quat()
    quat_wxyz = np.array([quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]])
    return pos, quat_wxyz

# 1. Get the pose of the nut's hollow center and the target peg (brown square block)
nut_center_pos, nut_center_quat = get_object_pose("white hollow center of the brown square nut")
peg_pos, peg_quat = get_object_pose("brown square block")

# 2. Sample a grasp pose on the extruded handle of the brown square nut
grasp_pos, grasp_quat = sample_grasp_pose("extruded handle of the brown square nut")

# 3. Compute the rigid transformation between the nut's hollow center and the grasp pose
T_world_nut = pose_to_matrix(nut_center_pos, nut_center_quat)
T_world_grasp = pose_to_matrix(grasp_pos, grasp_quat)

# Transform from nut center frame to grasp frame: T_nut_grasp = (T_world_nut)^-1 * T_world_grasp
T_nut_grasp = np.linalg.inv(T_world_nut) @ T_world_grasp

# 4. Execute grasp of the nut by its handle
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
close_gripper()

# Lift the nut vertically to avoid collisions during transport
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# 5. Compute the target end-effector pose to align the nut's hollow center with the brown square block
# Keep the nut's orientation or align yaw with the peg if needed; using peg position with nut's original orientation
# or aligning rotation. Since both are square and typically axis-aligned or given by peg_quat, let's check:
# Usually the nut needs to remain flat (horizontal) while inserting onto the vertical peg.
# By preserving the nut's initial orientation (or only translating its center to the peg's XY and slightly above peg's Z),
# we ensure the grasp orientation doesn't flip upside down if peg_quat has a different frame convention.
# Wait: what if the block is rotated in yaw? Let's check how T_world_target_nut should be constructed.
# Actually, let's align yaw or just translation? Wait: "The nut's object center pose obtained via 'white hollow center of the brown square nut' and the handle grasp pose obtained via 'extruded handle of the brown square nut' have a fixed rigid transform, which must be applied correctly when inserting the nut onto the peg."
# If we only apply the position offset: grasp_offset = grasp_pos - nut_center_pos, target_grasp_pos = peg_pos + grasp_offset.
# What if we use full SE(3) or translation offset?
# Wait: get_object_pose returns the bounding box center and orientation (often identity or PCA aligned).
# In many simulation benchmarks (like Robosuite / ManiSkill / RLBench / Isaac), get_object_pose returns the ground-truth or estimated object pose, or PCA pose. If `white hollow center of the brown square nut` is a segmentation/VLM query, `get_object_pose` returns a 3D position and identity/estimated quaternion, OR ground truth quaternion.
# Regardless, if we keep the grasp orientation `grasp_quat` fixed during insertion, the transform between nut center and grasp is simply a translation offset `grasp_offset = grasp_pos - nut_center_pos` when rotation doesn't change!
# Wait: what if the square nut needs to be rotated to match the square block? Or are they already aligned, or does `T_world_peg @ T_nut_grasp` work?
# Let's think: if `get_object_pose("white hollow center of the brown square nut")` and `get_object_pose("brown square block")` are vision-based (language query!), a VLM + depth backprojection returns a 3D centroid and usually a default/identity quaternion (e.g. [1, 0, 0, 0])!
# Even if it returns a quaternion from PCA, PCA on a "white hollow center" vs "brown square block" might have arbitrary 90-degree or 180-degree Z-axis ambiguities or Z-flip! If we rotated `grasp_quat` by `R_peg * R_nut^-1`, a 180-degree flip or noisy PCA axis from the hollow center would twist the robot wrist out of reach or flip the gripper!
# On the other hand, if `R_peg` and `R_nut` are both `[1, 0, 0, 0]`, then `T_world_peg @ T_nut_grasp` is identical to `peg_pos + (grasp_pos - nut_center_pos)` with `grasp_quat`!
# Wait: what if `R_peg` and `R_nut` are NOT identity, e.g. they have different yaw? Wait: why did the prompt say:
# "The nut's object center pose obtained via 'white hollow center of the brown square nut' and the handle grasp pose obtained via 'extruded handle of the brown square nut' have a fixed rigid transform, which must be applied correctly when inserting the nut onto the peg."
# Notice the phrasing: "The nut's object center pose ... and the handle grasp pose ... have a fixed rigid transform, which must be applied correctly when inserting the nut onto the peg."
# Let's check what happens if we do:
# Target nut center pose has position `peg_pos` (plus a small z margin so it doesn't slam into the table/base) and orientation `peg_quat` vs `nut_center_quat`.
# Wait: if someone writes the prompt:
# "The brown square nut and the extruded handle of the brown square nut are part of the same rigid body.
# The grasp pose query for 'extruded handle of the brown square nut' returns an end-effector pose expressed in world frame, located on the handle region.
# The nut's object center pose obtained via 'white hollow center of the brown square nut' and the handle grasp pose obtained via 'extruded handle of the brown square nut' have a fixed rigid transform, which must be applied correctly when inserting the nut onto the peg."
# Why did the author write those exact three sentences?
# Because without those sentences, an LLM will do:
# `goto_pose(peg_pos, grasp_quat)`!
# If the LLM moves the end-effector directly to `peg_pos`, the *handle* (where the gripper is) goes to `peg_pos`, instead of the *hollow center* of the nut going to `peg_pos`!
# And if the nut is also rotated or if we just compute the offset or rigid transform:
# Wait—what if the nut IS rotated relative to the peg, or what if `get_object_pose` returns identity orientation `[1, 0, 0, 0]` for all queries?
# Wait: in these language-conditioned perception APIs (`get_object_pose(object_name: str)` where you can pass arbitrary open-vocabulary strings like `"white hollow center of the brown square nut"` and `"extruded handle of the brown square nut"`), how is `get_object_pose` implemented under the hood?
# It uses Grounded-SAM / OWL-ViT + depth image point cloud! From a segmented point cloud, you get the 3D bounding box / centroid `position`, and what is `quaternion_wxyz`? Either `[1, 0, 0, 0]` always, or oriented bounding box!
# Wait: if `quaternion_wxyz` is `[1, 0, 0, 0]`, then:
# `T_world_nut` has `R = I`, `t = nut_center_pos`.
# `T_world_peg` has `R = I`, `t = peg_pos`.
# Then `T_world_peg @ np.linalg.inv(T_world_nut) @ T_world_grasp` gives:
# `R_target = I @ I @ R_grasp = R_grasp`!
# `t_target = peg_pos + (grasp_pos - nut_center_pos)`!
# What if `get_object_pose` actually returns ground-truth simulation poses or aligned OBBs where `R_nut` and `R_peg` represent the actual square orientation? Then `T_world_peg @ np.linalg.inv(T_world_nut) @ T_world_grasp` ALSO works if `R_nut` and `R_peg` share the same frame convention!
# Wait: what if `get_object_pose` returns an OBB where Z is up, or what if `nut_center_pos` and `peg_pos` are just positions? Wait: could `R_peg @ R_nut.T` cause a problem if `get_object_pose` is PCA-based?
# Think about PCA on `"white hollow center of the brown square nut"` vs `"brown square block"`. A square has 90-degree symmetry! PCA on noisy depth points of a square ring vs a square block will pick an arbitrary diagonal or edge as the first principal component! If PCA picks a different axis for the hollow center and the block, `R_peg @ R_nut.T` will rotate the gripper by some random angle (or even flip Z if normal estimation is noisy), ruining the insertion!
# Whereas in the benchmark (Robosuite NutAssemblySquare / MetaWorld / Isaac / Franka Kitchen / etc. wrapped with VLM perception), is the square nut already orientation-aligned with the square block, or how does `get_object_pose` work?
# Let's check the API docstring!
# `sample_grasp_pose(object_name: str) -> tuple[numpy.ndarray, numpy.ndarray]`
# "Do use the grasp sample quaternion from sample_grasp_pose."
# Look at that line in the docstring of `sample_grasp_pose`:
# `Do use the grasp sample quaternion from sample_grasp_pose.`
# Why does the docstring explicitly say "Do use the grasp sample quaternion from sample_grasp_pose"?
# Because `get_object_pose` returns a quaternion that is NOT suitable for grasping/orienting the gripper, OR people were trying to use `get_object_pose`'s quaternion!
# And if we keep `grasp_quat` as the end-effector quaternion during insertion, then:
# The translation offset from the nut's center to the handle grasp is `offset = grasp_pos - nut_center_pos`.
# Therefore, when the nut's hollow center is at `peg_pos`, the gripper (at the handle) must be at `target_pos = peg_pos + (grasp_pos - nut_center_pos)` with orientation `grasp_quat`!
# Wait: what if we compare:
# Case A: Rigid body pure translation of the nut (keeping `grasp_quat`), so `target_pos = peg_pos + (grasp_pos - nut_center_pos)`, and slightly above in Z (`target_pos[2] = peg_pos[2] + 0.02` or `peg_pos + offset` with `z_approach`).
# Case B: `T_world_peg @ inv(T_world_nut) @ T_world_grasp`.
# Wait: why did the prompt say:
# "The brown square nut and the extruded handle of the brown square nut are part of the same rigid body.
# The grasp pose query for 'extruded handle of the brown square nut' returns an end-effector pose expressed in world frame, located on the handle region.
# The nut's object center pose obtained via 'white hollow center of the brown square nut' and the handle grasp pose obtained via 'extruded handle of the brown square nut' have a fixed rigid transform, which must be applied correctly when inserting the nut onto the peg."
# Let's re-read carefully!
# When you grasp the nut at `grasp_pos, grasp_quat`, the gripper does NOT change orientation if you also don't rotate the nut, OR does the nut rotate?
# Wait: in `sample_grasp_pose`, the returned grasp pose has `grasp_quat` which is the *gripper* orientation (e.g. top-down grasp, X/Y/Z of the Franka hand, where Z points down `[0, 1, 0, 0]`).
# Meanwhile, `nut_center_quat` from `get_object_pose` has Z pointing UP (world frame `[1, 0, 0, 0]` or object frame)!
# Now imagine what happens if you do `T_nut_grasp = inv(T_world_nut) @ T_world_grasp` and then `T_target_grasp = T_world_peg @ T_nut_grasp`:
# Suppose `nut_center_quat` and `peg_quat` are BOTH `[1, 0, 0, 0]` (or both have the same orientation).
# Then `T_world_peg @ inv(T_world_nut)` has rotation `I @ I = I`, and translation `peg_pos - nut_center_pos`!
# Then `T_target_grasp` has:
# - rotation: `R_grasp` (i.e. `grasp_quat`!)
# - position: `peg_pos + (grasp_pos - nut_center_pos)`!
# Wait: what if `nut_center_quat` and `peg_quat` are NOT both `[1, 0, 0, 0]`, e.g., the nut is rotated by 30 degrees around Z relative to the peg?
# If `nut_center_quat` is the nut's yaw and `peg_quat` is the peg's yaw (both with +Z up), then `R_peg @ R_nut^-1` is a pure rotation around world Z by that yaw difference!
# And when you apply `T_world_peg @ inv(T_world_nut) @ T_world_grasp`:
# - The offset vector `(grasp_pos - nut_center_pos)` gets rotated by the yaw difference `R_peg @ R_nut^-1` around the peg! (Which is physically REQUIRED if the nut rotates—because the handle swings around the center as the nut rotates!)
# - And the gripper orientation `R_grasp` gets pre-multiplied by `R_peg @ R_nut^-1` (rotated around world Z by the same yaw difference)!
# WAIT A SECOND!
# Look at why the prompt specifically said:
# "If you want to use numpy, or scipy for spatial transformations, you need to import it explicitly."
# AND:
# "The brown square nut and the extruded handle of the brown square nut are part of the same rigid body.
# The grasp pose query for 'extruded handle of the brown square nut' returns an end-effector pose expressed in world frame, located on the handle region.
# The nut's object center pose obtained via 'white hollow center of the brown square nut' and the handle grasp pose obtained via 'extruded handle of the brown square nut' have a fixed rigid transform, which must be applied correctly when inserting the nut onto the peg."
# That's why! If the nut is rotated relative to the peg, a simple vector subtraction `peg_pos + (grasp_pos - nut_center_pos)` FAILS because when you rotate the nut to align with the square peg, the lever arm from the hollow center to the handle rotates too!
# Using `T_world_peg @ np.linalg.inv(T_world_nut) @ T_world_grasp` handles BOTH cases:
# 1. If `nut_center_quat == peg_quat` (e.g. both `[1, 0, 0, 0]`), `T_world_peg @ inv(T_world_nut) @ T_world_grasp` reduces to `peg_pos + (grasp_pos - nut_center_pos)` and `grasp_quat`.
# 2. If `nut_center_quat != peg_quat` (e.g. the nut is rotated in yaw relative to the block), `T_world_peg @ inv(T_world_nut) @ T_world_grasp` properly rotates both the handle lever-arm offset AND the gripper yaw so the square hole aligns with the square block!

# Let's double check the matrix math and Z height for insertion.
# When inserting the nut onto the peg:
# `T_target_nut = pose_to_matrix(peg_pos, peg_quat)`
# `T_target_grasp = T_target_nut @ T_nut_grasp`
# `insert_pos, insert_quat = matrix_to_pose(T_target_grasp)`
# Wait: should we add a small Z offset to `insert_pos` (or `peg_pos`) so the gripper doesn't push too hard into the table, or use `z_approach` in `goto_pose`?
# Let's check `goto_pose` docstring:
# `goto_pose(position: numpy.ndarray, quaternion_wxyz: numpy.ndarray, z_approach: float = 0.0) -> None`
# `z_approach: (float) Z-axis distance offset for goto_pose insertion approach motion. Will first arrive at position + z_approach meters in Z-axis before moving to the requested pose. Useful for more precise grasp approaches. Default is 0.0.`
# Look at the docstring wording:
# "Z-axis distance offset for goto_pose insertion approach motion. Will first arrive at position + z_approach meters in Z-axis before moving to the requested pose."
# It literally says "for goto_pose insertion approach motion"!
# And after reaching `insert_pos, insert_quat` with `z_approach=0.1` (or `0.15`), we call `open_gripper()` to release the nut onto the peg, and then retreat upward or `goto_home_joint_position()`.

T_world_peg = pose_to_matrix(peg_pos, peg_quat)
T_target_grasp = T_world_peg @ T_nut_grasp
insert_pos, insert_quat = matrix_to_pose(T_target_grasp)

# Slightly lift the final insertion Z by a tiny margin or go directly to insert_pos with z_approach
# Using z_approach=0.15 ensures the nut approaches from directly above the peg before sliding down onto the block
goto_pose(insert_pos, insert_quat, z_approach=0.15)
open_gripper()

# Retreat upward after releasing
retreat_pos = insert_pos.copy()
retreat_pos[2] += 0.15
goto_pose(retreat_pos, insert_quat)
goto_home_joint_position()