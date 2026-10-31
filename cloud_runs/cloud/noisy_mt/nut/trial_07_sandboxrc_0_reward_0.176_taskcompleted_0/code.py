# Code block 0
import numpy as np

def avg_pose(name, fn, n=10):
    # Average several perception calls to reduce ~1cm noise.
    ps = []
    q0 = None
    for _ in range(n):
        p, q = fn(name)
        ps.append(p)
        if q0 is None:
            q0 = q
    return np.mean(ps, axis=0), q0

# Reset arm and open gripper
goto_home_joint_position()
open_gripper()

# Perceive the handle grasp pose and the nut center pose (averaged)
grasp_pos, grasp_quat = avg_pose("extruded handle of the brown square nut", sample_grasp_pose)
nut_pos, _ = avg_pose("white hollow center of the brown square nut", get_object_pose)

# Fixed rigid offset from nut center to the handle grasp point (world frame).
# The gripper orientation is kept constant throughout, so this offset stays valid.
offset = grasp_pos - nut_pos

# Grasp the handle with a vertical approach
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift the nut well above the peg height
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.20
goto_pose(lift_pos, grasp_quat)

# Perceive the peg (averaged)
peg_pos, _ = avg_pose("brown square block", get_object_pose)

# Target nut center: aligned with peg XY, slightly above peg base so it slides down the peg.
target_nut = peg_pos.copy()
target_nut[2] = peg_pos[2] + 0.01

# Corresponding gripper position via the rigid offset
target_grasp = target_nut + offset

# Move above the peg, then insert with a vertical approach
above = target_grasp.copy()
above[2] = lift_pos[2]
goto_pose(above, grasp_quat)
goto_pose(target_grasp, grasp_quat, z_approach=0.15)

# Release and retreat
open_gripper()
retreat = target_grasp.copy()
retreat[2] += 0.15
goto_pose(retreat, grasp_quat)
goto_home_joint_position()