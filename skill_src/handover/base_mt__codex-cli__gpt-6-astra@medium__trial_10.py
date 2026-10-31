# Code block 0
import numpy as np

q0_pick = np.array([0.0, 2**-0.5, 2**-0.5, 0.0])
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1_transfer = np.array([0.0, 0.0, 1.0, 0.0])

hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
clearance_z = max(0.35, hammer_initial[2] + 0.20)
handover_center = np.array([0.81, 0.0, 0.175])
grasp_offset = 0.05

def translate(move, start, finish, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    finish = np.asarray(finish, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(finish - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (finish - start), quaternion)
    return finish.copy()

# Keep Arm 1 on its own side until the hammer is positioned.
open_gripper_arm1()
p1 = np.array([1.18, 0.0, clearance_z])
goto_pose_arm1(p1, q1_transfer)

open_gripper_arm0()
p0 = np.array([0.44, 0.0, clearance_z])
goto_pose_arm0(p0, q0_pick)

# Grasp the head-side portion of the handle, leaving its other end free.
pickup = hammer_initial + np.array([0.0, -grasp_offset, 0.0])
above_pickup = pickup.copy()
above_pickup[2] = clearance_z
p0 = translate(goto_pose_arm0, p0, above_pickup, q0_pick)
p0 = translate(goto_pose_arm0, p0, pickup, q0_pick, step=0.01)
close_gripper_arm0()

p0 = translate(goto_pose_arm0, p0, above_pickup, q0_pick)
hammer_lifted = np.asarray(get_hammer_pose()[0], dtype=float)
expected_lift = clearance_z - pickup[2]
if abs((hammer_lifted[2] - hammer_initial[2]) - expected_lift) > 0.035:
    raise RuntimeError("Hammer lift was not confirmed; do not cross the gap.")

# Rotate in place above the pickup region: the handle now points +X.
# Arm 0 holds the left end; Arm 1 receives the right end.
for angle in np.linspace(np.pi / 4.0, 0.0, 13)[1:]:
    quaternion = np.array([0.0, np.cos(angle), np.sin(angle), 0.0])
    goto_pose_arm0(p0, quaternion)

hammer_rotated = np.asarray(get_hammer_pose()[0], dtype=float)
center_offset = hammer_rotated - p0
high_center = handover_center.copy()
high_center[2] = clearance_z
high_transfer = high_center - center_offset

p0 = translate(goto_pose_arm0, p0, high_transfer, q0_transfer)
low_transfer = handover_center - center_offset
p0 = translate(goto_pose_arm0, p0, low_transfer, q0_transfer, step=0.01)

hammer_now = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= hammer_now[2] <= 0.20:
    raise RuntimeError("Hammer is outside the required handover height.")

receive = hammer_now + np.array([grasp_offset, 0.0, 0.0])
if np.linalg.norm(receive[:2] - p0[:2]) < 0.085:
    raise RuntimeError("Insufficient gripper clearance for transfer.")

# Approach vertically with approximately 10 cm horizontal separation.
above_receive = receive.copy()
above_receive[2] = clearance_z
p1 = translate(goto_pose_arm1, p1, above_receive, q1_transfer)
p1 = translate(goto_pose_arm1, p1, receive, q1_transfer, step=0.01)

# Never release the donor before closing the receiver.
close_gripper_arm1()
open_gripper_arm0()

retreat = p0.copy()
retreat[2] = clearance_z
p0 = translate(goto_pose_arm0, p0, retreat, q0_transfer, step=0.01)
p0 = translate(
    goto_pose_arm0,
    p0,
    np.array([0.44, 0.0, clearance_z]),
    q0_transfer,
)