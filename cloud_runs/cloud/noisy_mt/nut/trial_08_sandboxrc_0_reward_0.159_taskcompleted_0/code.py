# Code block 0
import numpy as np

def avg_pose(name, n=5):
    ps, qs = [], []
    for _ in range(n):
        p, q = get_object_pose(name)
        ps.append(p); qs.append(q)
    return np.mean(ps, axis=0), qs[0]

def avg_grasp(name, n=5):
    ps, qs = [], []
    for _ in range(n):
        p, q = sample_grasp_pose(name)
        ps.append(p); qs.append(q)
    return np.mean(ps, axis=0), qs[0]

goto_home_joint_position()
open_gripper()

# Perceive (average several noisy calls)
nut_center_pos, _ = avg_pose('white hollow center of the brown square nut')
block_pos, _ = avg_pose('brown square block')
grasp_pos, grasp_quat = avg_grasp('extruded handle of the brown square nut')

# Rigid offset from nut center to handle grasp (world frame; gripper orientation is kept fixed during transport)
offset = grasp_pos - nut_center_pos

# Grasp the handle
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.20
goto_pose(lift_pos, grasp_quat)

# Target: nut center over the block/peg, keeping the same handle offset
target_center = block_pos.copy()
target_center[2] = block_pos[2] + 0.02
target_grasp = target_center + offset

# Move above the peg, then insert by descending
goto_pose(target_grasp, grasp_quat, z_approach=0.20)

# Release nut onto the peg
open_gripper()

# Retreat
retreat = target_grasp.copy()
retreat[2] += 0.15
goto_pose(retreat, grasp_quat)
goto_home_joint_position()

# Code block 1
import numpy as np

def avg_pose(name, n=8):
    ps = [get_object_pose(name)[0] for _ in range(n)]
    return np.mean(ps, axis=0)

nut_c = avg_pose('white hollow center of the brown square nut')
blk = avg_pose('brown square block')
xy_err = np.linalg.norm(nut_c[:2] - blk[:2])
print('nut center:', nut_c)
print('block:', blk)
print('xy error (m):', xy_err, 'z diff (m):', nut_c[2] - blk[2])

if xy_err > 0.015:
    # Not inserted well: re-grasp the handle and retry with the nut lowered fully onto the peg
    goto_home_joint_position()
    open_gripper()
    gps, gqs = [], []
    for _ in range(6):
        p, q = sample_grasp_pose('extruded handle of the brown square nut')
        gps.append(p); gqs.append(q)
    grasp_pos, grasp_quat = np.mean(gps, axis=0), gqs[0]
    nut_c = avg_pose('white hollow center of the brown square nut')
    offset = grasp_pos - nut_c

    goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
    close_gripper()
    lift = grasp_pos.copy(); lift[2] += 0.20
    goto_pose(lift, grasp_quat)

    blk = avg_pose('brown square block')
    target_center = blk.copy()
    target_center[2] = blk[2] + 0.01
    target_grasp = target_center + offset
    goto_pose(target_grasp, grasp_quat, z_approach=0.20)
    open_gripper()
    retreat = target_grasp.copy(); retreat[2] += 0.15
    goto_pose(retreat, grasp_quat)
    goto_home_joint_position()

    nut_c = avg_pose('white hollow center of the brown square nut')
    blk = avg_pose('brown square block')
    print('after retry xy error (m):', np.linalg.norm(nut_c[:2] - blk[:2]), 'z diff:', nut_c[2] - blk[2])

# Code block 2
import numpy as np

def avg_pose(name, n=15):
    ps = [get_object_pose(name)[0] for _ in range(n)]
    return np.mean(ps, axis=0)

goto_home_joint_position()
open_gripper()

# Re-grasp the handle
gps, gqs = [], []
for _ in range(10):
    p, q = sample_grasp_pose('extruded handle of the brown square nut')
    gps.append(p); gqs.append(q)
grasp_pos, grasp_quat = np.mean(gps, axis=0), gqs[0]

goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift to a known commanded pose and measure the nut center while held.
# This gives the actual rigid offset between the gripper (commanded pose) and the nut center,
# which cancels any bias between the grasp sampler and the object-center perception.
lift = grasp_pos.copy(); lift[2] += 0.20
goto_pose(lift, grasp_quat)
nut_c_held = avg_pose('white hollow center of the brown square nut', n=20)
offset = lift - nut_c_held
print('measured gripper->nut-center offset:', offset)

# Target: nut center directly over the block/peg, descend to insert
blk = avg_pose('brown square block', n=20)
target_center = blk.copy()
target_center[2] = blk[2] + 0.005
target_grasp = target_center + offset
goto_pose(target_grasp, grasp_quat, z_approach=0.20)
open_gripper()

retreat = target_grasp.copy(); retreat[2] += 0.15
goto_pose(retreat, grasp_quat)
goto_home_joint_position()

nut_c = avg_pose('white hollow center of the brown square nut', n=20)
blk = avg_pose('brown square block', n=20)
print('nut center:', nut_c)
print('block:', blk)
print('xy error (m):', np.linalg.norm(nut_c[:2] - blk[:2]), 'z diff:', nut_c[2] - blk[2])