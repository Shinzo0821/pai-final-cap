# Code block 0
import numpy as np

q0_pick = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q0_pass = np.array([0.0, 1.0, 0.0, 0.0])
q1_pass = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer_initial, _ = get_hammer_pose()
hammer_initial = np.asarray(hammer_initial, dtype=float)

# Both grasp sites remain inside even the shortest handle.
# After rotation, the head points toward Arm 0 and the free handle toward Arm 1.
offset = 0.052
safe_z = max(0.36, hammer_initial[2] + 0.20)
midpoint = np.array([0.81, 0.0, 0.175])

open_gripper_arm1()
p1 = np.array([1.18, 0.0, safe_z])
goto_pose_arm1(p1, q1_pass)

open_gripper_arm0()
grasp0 = hammer_initial + np.array([0.0, -offset, 0.0])
p0 = np.array([grasp0[0], grasp0[1], safe_z])
goto_pose_arm0(p0, q0_pick)
p0 = translate(goto_pose_arm0, p0, grasp0, q0_pick)
close_gripper_arm0()

p0 = translate(
    goto_pose_arm0, p0,
    np.array([p0[0], p0[1], safe_z]),
    q0_pick
)

hammer_lifted, _ = get_hammer_pose()
hammer_lifted = np.asarray(hammer_lifted, dtype=float)
if hammer_lifted[2] < hammer_initial[2] + 0.08:
    raise RuntimeError("Pickup failed; do not move the hammer over the gap.")

# Rotate in place above the pickup area, before translating toward the other arm.
for angle in np.linspace(np.pi / 4.0, 0.0, 19)[1:]:
    quaternion = np.array([0.0, np.cos(angle), np.sin(angle), 0.0])
    goto_pose_arm0(p0, quaternion)

hammer_rotated, _ = get_hammer_pose()
hammer_rotated = np.asarray(hammer_rotated, dtype=float)
target0 = p0 + np.array([
    midpoint[0] - hammer_rotated[0],
    midpoint[1] - hammer_rotated[1],
    0.0
])
p0 = translate(goto_pose_arm0, p0, target0, q0_pass)

# Control the measured handle-center height, not an assumed table-relative height.
for _ in range(3):
    hammer, _ = get_hammer_pose()
    hammer = np.asarray(hammer, dtype=float)
    error = midpoint - hammer
    if np.linalg.norm(error) < 0.003:
        break
    p0 = translate(goto_pose_arm0, p0, p0 + error, q0_pass)

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
if not 0.15 <= hammer[2] <= 0.20:
    raise RuntimeError("Hammer is outside the handover height range.")

grasp1 = hammer + np.array([offset, 0.0, 0.0])
if np.linalg.norm(grasp1 - p0) < 0.09:
    raise RuntimeError("Insufficient separation between grasp sites.")

# Arm 1 approaches vertically on the free-handle side.
above1 = np.array([grasp1[0], grasp1[1], safe_z])
p1 = translate(goto_pose_arm1, p1, above1, q1_pass)
p1 = translate(goto_pose_arm1, p1, grasp1, q1_pass)
close_gripper_arm1()

# Never release the donor before the receiving gripper has closed.
open_gripper_arm0()
p0 = translate(
    goto_pose_arm0, p0,
    p0 + np.array([0.0, 0.0, 0.16]),
    q0_pass
)
p0 = translate(
    goto_pose_arm0, p0,
    p0 + np.array([-0.15, 0.0, 0.0]),
    q0_pass
)