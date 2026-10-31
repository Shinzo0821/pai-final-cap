# Code block 0
import numpy as np

q0 = np.array([0.0, 1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for t in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + t * (end - start), quaternion)
    return end.copy()

def rotate_z(quaternion, angle):
    w, x, y, z = quaternion
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    result = np.array([c*w - s*z, c*x - s*y, c*y + s*x, c*z + s*w])
    return result / np.linalg.norm(result)

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

open_gripper_arm0()
open_gripper_arm1()

# Keep the receiving arm away from the pickup and rotation workspace.
park1 = np.array([1.18, 0.0, max(0.40, hammer[2] + 0.25)])
goto_pose_arm1(park1, q1)

# Grasp the head-side portion of the handle, reserving its other end.
grasp0 = hammer + np.array([0.0, -0.045, 0.0])
clearance_z = max(0.34, hammer[2] + 0.20)
p0 = grasp0.copy()
p0[2] = clearance_z
goto_pose_arm0(p0, q0)
p0 = translate(goto_pose_arm0, p0, grasp0, q0, step=0.01)
close_gripper_arm0()

lift = p0.copy()
lift[2] = clearance_z
p0 = translate(goto_pose_arm0, p0, lift, q0)

lifted_hammer, _ = get_hammer_pose()
lifted_hammer = np.asarray(lifted_hammer, dtype=float)
if lifted_hammer[2] < hammer[2] + 0.06:
    raise RuntimeError("Hammer did not lift; refusing to move over the gap.")

# Rotate in place at clearance height: handle +Y becomes handle +X.
# Both grippers will then close across Y, approaching from opposite sides.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    goto_pose_arm0(p0, rotate_z(q0, angle))
q0 = rotate_z(q0, -np.pi / 2.0)

# Position the measured handle midpoint at the inter-arm midpoint.
handover = np.array([0.81, 0.0, 0.175])
current_hammer, _ = get_hammer_pose()
current_hammer = np.asarray(current_hammer, dtype=float)

high_target = handover.copy()
high_target[2] = clearance_z
target0 = p0 + high_target - current_hammer

# Translate laterally before lowering; never combine rotation and translation.
lateral0 = target0.copy()
lateral0[2] = p0[2]
p0 = translate(goto_pose_arm0, p0, lateral0, q0)
p0 = translate(goto_pose_arm0, p0, target0, q0)

current_hammer, _ = get_hammer_pose()
target0 = p0 + handover - np.asarray(current_hammer, dtype=float)
p0 = translate(goto_pose_arm0, p0, target0, q0, step=0.01)

current_hammer, _ = get_hammer_pose()
current_hammer = np.asarray(current_hammer, dtype=float)
if not 0.15 <= current_hammer[2] <= 0.20:
    raise RuntimeError("Hammer is outside the handover height window.")

# These handle grasp locations are approximately 10.5 cm apart.
grasp1 = current_hammer + np.array([0.060, 0.0, 0.0])
if np.linalg.norm((grasp1 - p0)[:2]) < 0.095:
    raise RuntimeError("Insufficient gripper separation for a safe handover.")

above1 = grasp1.copy()
above1[2] = max(park1[2], p0[2] + 0.18)
p1 = translate(goto_pose_arm1, park1, above1, q1)
p1 = translate(goto_pose_arm1, p1, grasp1, q1, step=0.01)
close_gripper_arm1()

# Maintain the receiving grasp before releasing the supporting arm.
open_gripper_arm0()
retreat0 = p0 + np.array([0.0, 0.0, 0.18])
p0 = translate(goto_pose_arm0, p0, retreat0, q0, step=0.01)
retreat0 = p0 + np.array([-0.16, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat0, q0)