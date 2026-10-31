# Code block 0
import numpy as np

# --- Helper: average several noisy perception calls to reduce ~1cm error ---
def avg_pose(fn, name, n=8):
    ps, qs = [], []
    for _ in range(n):
        p, q = fn(name)
        ps.append(p); qs.append(q)
    return np.mean(ps, axis=0), qs[0]

# --- Perceive nut handle grasp, nut center, and peg ---
grasp_pos, grasp_quat = avg_pose(sample_grasp_pose, "extruded handle of the brown square nut")
nut_pos, _ = avg_pose(get_object_pose, "white hollow center of the brown square nut")
peg_pos, _ = avg_pose(get_object_pose, "brown square block")

# Rigid offset from nut center to end-effector (world frame); orientation is held fixed during transport
offset = grasp_pos - nut_pos

# --- Grasp the nut by its handle ---
goto_home_joint_position()
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# --- Lift ---
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.20
goto_pose(lift_pos, grasp_quat)

# --- Move above peg so nut center aligns with peg, then insert along -Z ---
target_pos = peg_pos + offset
target_pos[2] = nut_pos[2] + offset[2] + 0.005  # bring nut down to table-level around the peg
above_pos = target_pos.copy()
above_pos[2] += 0.20
goto_pose(above_pos, grasp_quat)
goto_pose(target_pos, grasp_quat, z_approach=0.15)

# --- Release and retreat ---
open_gripper()
goto_pose(above_pos, grasp_quat)
goto_home_joint_position()

# Code block 1
import numpy as np

# Verify insertion: nut center should be horizontally aligned with the peg
nut_p = np.mean([get_object_pose("white hollow center of the brown square nut")[0] for _ in range(8)], axis=0)
peg_p = np.mean([get_object_pose("brown square block")[0] for _ in range(8)], axis=0)
dxy = np.linalg.norm(nut_p[:2] - peg_p[:2])
print("nut center:", nut_p)
print("peg:", peg_p)
print("xy distance nut->peg: %.4f m" % dxy)
print("INSERTED" if dxy < 0.02 else "NOT_INSERTED")

# Code block 2
import numpy as np

def avg_pos(fn, name, n=12):
    ps, qs = [], []
    for _ in range(n):
        p, q = fn(name)
        ps.append(p); qs.append(q)
    return np.mean(ps, axis=0), qs[0]

# --- Re-perceive nut (currently resting on table, misplaced) and peg ---
grasp_pos, grasp_quat = avg_pos(sample_grasp_pose, "extruded handle of the brown square nut")
nut_rest, _ = avg_pos(get_object_pose, "white hollow center of the brown square nut")
peg_pos, _ = avg_pos(get_object_pose, "brown square block")
rest_z = nut_rest[2]  # nut-center height when sitting on the table

# --- Regrasp by the handle ---
goto_home_joint_position()
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# --- Lift to a known EE pose and re-measure the nut while held (accounts for slip during grasp) ---
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.20
goto_pose(lift_pos, grasp_quat)
nut_held, _ = avg_pos(get_object_pose, "white hollow center of the brown square nut", n=16)
offset = lift_pos - nut_held  # EE relative to nut center (world frame, orientation held fixed)

# --- Align nut center over peg, descend straight down onto it ---
target_pos = peg_pos + offset
target_pos[2] = rest_z + offset[2] + 0.003
above_pos = target_pos.copy()
above_pos[2] += 0.20
goto_pose(above_pos, grasp_quat)

# Fine correction above peg: re-measure held nut vs peg and shift laterally
nut_above, _ = avg_pos(get_object_pose, "white hollow center of the brown square nut", n=12)
peg_chk, _ = avg_pos(get_object_pose, "brown square block", n=12)
corr = peg_chk[:2] - nut_above[:2]
above_pos[:2] += corr
target_pos[:2] += corr
goto_pose(above_pos, grasp_quat)
goto_pose(target_pos, grasp_quat, z_approach=0.15)

# --- Release and retreat ---
open_gripper()
goto_pose(above_pos, grasp_quat)
goto_home_joint_position()

# --- Verify ---
nut_p = np.mean([get_object_pose("white hollow center of the brown square nut")[0] for _ in range(12)], axis=0)
peg_p = np.mean([get_object_pose("brown square block")[0] for _ in range(12)], axis=0)
dxy = np.linalg.norm(nut_p[:2] - peg_p[:2])
print("nut center:", nut_p)
print("peg:", peg_p)
print("xy distance nut->peg: %.4f m" % dxy)
print("INSERTED" if dxy < 0.02 else "NOT_INSERTED")