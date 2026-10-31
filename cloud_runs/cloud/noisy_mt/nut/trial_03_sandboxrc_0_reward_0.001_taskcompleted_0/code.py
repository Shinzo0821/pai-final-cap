# Code block 0
import numpy as np

def avg_pose(name, n=8):
    ps = []
    q0 = None
    for _ in range(n):
        p, q = get_object_pose(name)
        ps.append(p)
        if q0 is None:
            q0 = q
    return np.mean(ps, axis=0), q0

def avg_grasp(name, n=8):
    ps = []
    q0 = None
    for _ in range(n):
        p, q = sample_grasp_pose(name)
        ps.append(p)
        if q0 is None:
            q0 = q
    return np.mean(ps, axis=0), q0

# Perceive nut center, handle grasp, and block (averaged to reduce noise)
nut_center_pos, _ = avg_pose("white hollow center of the brown square nut")
grasp_pos, grasp_quat = avg_grasp("extruded handle of the brown square nut")
block_pos, _ = avg_pose("brown square block")

# Fixed rigid offset from nut center to handle grasp (world frame; orientation is kept constant)
offset = grasp_pos - nut_center_pos

# Grasp the handle
goto_home_joint_position()
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Move so that nut center aligns with the block peg, then insert from above
target_pos = block_pos + offset
target_pos[2] = grasp_pos[2] + 0.005  # keep handle at table-level grasp height for full insertion
above_pos = target_pos.copy()
above_pos[2] += 0.15
goto_pose(above_pos, grasp_quat)
goto_pose(target_pos, grasp_quat, z_approach=0.12)

# Release
open_gripper()
retreat = target_pos.copy()
retreat[2] += 0.12
goto_pose(retreat, grasp_quat)
goto_home_joint_position()