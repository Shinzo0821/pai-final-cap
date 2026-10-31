# Code block 0
import numpy as np

def avg_pose(fn, name, n=10):
    # average positions over multiple noisy perception calls; keep first quaternion
    pos_list = []
    quat = None
    for _ in range(n):
        p, q = fn(name)
        pos_list.append(p)
        if quat is None:
            quat = q
    return np.mean(np.array(pos_list), axis=0), quat

goto_home_joint_position()
open_gripper()

# Perceive the nut handle grasp, nut center, and block (averaged to reduce noise)
grasp_pos, grasp_quat = avg_pose(sample_grasp_pose, "extruded handle of the brown square nut")
nut_center_pos, _ = avg_pose(get_object_pose, "white hollow center of the brown square nut")
block_pos, _ = avg_pose(get_object_pose, "brown square block")

# Fixed rigid offset from nut center to grasp point (world frame; orientation is kept constant during transport)
offset = grasp_pos - nut_center_pos

# Grasp the nut by its handle, approaching from above
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Target: nut center over the block/peg, so end-effector goes to block + offset
target_pos = block_pos + offset
above_pos = target_pos.copy()
above_pos[2] += 0.15
goto_pose(above_pos, grasp_quat)

# Insert by descending straight down onto the peg
goto_pose(target_pos, grasp_quat, z_approach=0.15)

open_gripper()
retreat = target_pos.copy()
retreat[2] += 0.15
goto_pose(retreat, grasp_quat)
goto_home_joint_position()

# Code block 1
import numpy as np

# Verification only: check whether the nut is now seated on the block (no further motion).
nut_samples = np.array([get_object_pose("white hollow center of the brown square nut")[0] for _ in range(10)])
block_samples = np.array([get_object_pose("brown square block")[0] for _ in range(10)])
nut_c = nut_samples.mean(axis=0)
block_c = block_samples.mean(axis=0)
print("nut center:", nut_c)
print("block:", block_c)
print("xy distance:", np.linalg.norm(nut_c[:2] - block_c[:2]))
print("z diff (nut - block):", nut_c[2] - block_c[2])

# Code block 2
import numpy as np

def avg_pose(fn, name, n=20):
    pos_list = []
    quat = None
    for _ in range(n):
        p, q = fn(name)
        pos_list.append(p)
        if quat is None:
            quat = q
    return np.mean(np.array(pos_list), axis=0), quat

goto_home_joint_position()
open_gripper()

# Re-perceive everything (nut was not placed; it is ~35 cm from block)
grasp_pos, grasp_quat = avg_pose(sample_grasp_pose, "extruded handle of the brown square nut")
nut_center_pos, _ = avg_pose(get_object_pose, "white hollow center of the brown square nut")
block_pos, _ = avg_pose(get_object_pose, "brown square block")
print("grasp:", grasp_pos, "nut center:", nut_center_pos, "block:", block_pos)

# Rigid offset from nut center to handle grasp point (orientation held constant during transport)
offset = grasp_pos - nut_center_pos

# Grasp handle from above, slightly lower to ensure fingers wrap the handle
grasp_target = grasp_pos.copy()
grasp_target[2] -= 0.005
goto_pose(grasp_target, grasp_quat, z_approach=0.12)
close_gripper()

# Lift and verify nut came along
lift_pos = grasp_target.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)
nut_after_lift, _ = avg_pose(get_object_pose, "white hollow center of the brown square nut")
print("nut after lift:", nut_after_lift, "dz:", nut_after_lift[2] - nut_center_pos[2])

# Move above the block, then descend straight down onto the peg
target_pos = block_pos + offset
above_pos = target_pos.copy()
above_pos[2] += 0.15
goto_pose(above_pos, grasp_quat)

# Intermediate descent for precision, then final insertion
mid_pos = target_pos.copy()
mid_pos[2] += 0.05
goto_pose(mid_pos, grasp_quat)
goto_pose(target_pos, grasp_quat, z_approach=0.05)

open_gripper()
retreat = target_pos.copy()
retreat[2] += 0.15
goto_pose(retreat, grasp_quat)
goto_home_joint_position()

# Verify
nut_c, _ = avg_pose(get_object_pose, "white hollow center of the brown square nut")
block_c, _ = avg_pose(get_object_pose, "brown square block")
print("nut center:", nut_c, "block:", block_c)
print("xy distance:", np.linalg.norm(nut_c[:2] - block_c[:2]))
print("z diff (nut - block):", nut_c[2] - block_c[2])

# Code block 3
import numpy as np

def avg_pose(fn, name, n=20):
    pos_list = []
    quat = None
    for _ in range(n):
        p, q = fn(name)
        pos_list.append(p)
        if quat is None:
            quat = q
    return np.mean(np.array(pos_list), axis=0), quat

# Previous attempt: gripper closed but nut did not come along (dz ~ 0). Likely grasp too high / missed handle.
# Strategy: retry grasp with progressively deeper z, verifying lift each time.
success = False
for depth in [0.02, 0.03, 0.04]:
    goto_home_joint_position()
    open_gripper()
    grasp_pos, grasp_quat = avg_pose(sample_grasp_pose, "extruded handle of the brown square nut")
    nut_center_pos, _ = avg_pose(get_object_pose, "white hollow center of the brown square nut")
    block_pos, _ = avg_pose(get_object_pose, "brown square block")
    offset = grasp_pos - nut_center_pos
    print("depth", depth, "grasp:", grasp_pos, "nut center:", nut_center_pos, "block:", block_pos)

    grasp_target = grasp_pos.copy()
    grasp_target[2] -= depth
    goto_pose(grasp_target, grasp_quat, z_approach=0.12)
    close_gripper()

    lift_pos = grasp_target.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)
    nut_after_lift, _ = avg_pose(get_object_pose, "white hollow center of the brown square nut")
    dz = nut_after_lift[2] - nut_center_pos[2]
    print("nut after lift:", nut_after_lift, "dz:", dz)
    if dz > 0.05:
        success = True
        break
    # Failed: release and retry
    open_gripper()

if success:
    # Recompute offset using actual grasp height used (rigid in world frame since orientation unchanged)
    offset = grasp_target - nut_center_pos
    target_pos = block_pos + offset
    above_pos = target_pos.copy()
    above_pos[2] += 0.15
    goto_pose(above_pos, grasp_quat)
    mid_pos = target_pos.copy()
    mid_pos[2] += 0.05
    goto_pose(mid_pos, grasp_quat)
    goto_pose(target_pos, grasp_quat, z_approach=0.05)
    open_gripper()
    retreat = target_pos.copy()
    retreat[2] += 0.15
    goto_pose(retreat, grasp_quat)
    goto_home_joint_position()

    nut_c, _ = avg_pose(get_object_pose, "white hollow center of the brown square nut")
    block_c, _ = avg_pose(get_object_pose, "brown square block")
    print("nut center:", nut_c, "block:", block_c)
    print("xy distance:", np.linalg.norm(nut_c[:2] - block_c[:2]))
    print("z diff (nut - block):", nut_c[2] - block_c[2])
else:
    print("GRASP FAILED at all depths")
    goto_home_joint_position()