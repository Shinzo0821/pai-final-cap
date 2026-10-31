# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
safe_z = max(0.38, float(hammer[2]) + 0.22)
handover_center = np.array([0.81, 0.0, 0.175])
grasp_offset = 0.055

def translate(move, start, finish, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    finish = np.asarray(finish, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(finish - start) / step)))
    for i in range(1, count + 1):
        move(start + (finish - start) * (i / count), quaternion)
    return finish.copy()

# Keep the receiving arm outside the transfer corridor.
open_gripper_arm1()
park1 = np.array([1.18, 0.0, safe_z + 0.12])
goto_pose_arm1(park1, q1)

# Grasp the head-side portion of the handle, leaving its other end free.
open_gripper_arm0()
pickup = hammer + np.array([0.0, -grasp_offset, 0.0])
p0 = pickup.copy()
p0[2] = safe_z
goto_pose_arm0(p0, q0_pick)
p0 = translate(goto_pose_arm0, p0, pickup, q0_pick)
close_gripper_arm0()

lift = p0.copy()
lift[2] = safe_z
p0 = translate(goto_pose_arm0, p0, lift, q0_pick)

# Rotate in place above the pickup area: the handle now points toward +X.
# The two arms can consequently hold opposite ends without crossing wrists.
for angle in np.linspace(0.0, -np.pi / 2.0, 13)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    q = np.array([0.0, (c - s) / np.sqrt(2.0),
                  (c + s) / np.sqrt(2.0), 0.0])
    goto_pose_arm0(p0, q)

# Use the measured handle center rather than the unreliable object quaternion.
actual, _ = get_hammer_pose()
actual = np.asarray(actual, dtype=float)
desired_high = handover_center.copy()
desired_high[2] = safe_z
destination = p0 + desired_high - actual

vertical = p0.copy()
vertical[2] = destination[2]
p0 = translate(goto_pose_arm0, p0, vertical, q0_transfer)
p0 = translate(goto_pose_arm0, p0, destination, q0_transfer)

actual, _ = get_hammer_pose()
destination = p0 + handover_center - np.asarray(actual, dtype=float)
horizontal = p0.copy()
horizontal[:2] = destination[:2]
p0 = translate(goto_pose_arm0, p0, horizontal, q0_transfer)
p0 = translate(goto_pose_arm0, p0, destination, q0_transfer)

# Correct the actual hammer height before bringing in the receiving gripper.
actual, _ = get_hammer_pose()
correction = np.array([0.0, 0.0, 0.175 - float(actual[2])])
p0 = translate(goto_pose_arm0, p0, p0 + correction, q0_transfer)

actual, _ = get_hammer_pose()
receive = np.asarray(actual, dtype=float) + np.array([grasp_offset, 0.0, 0.0])
if np.linalg.norm(receive[:2] - p0[:2]) < 0.09:
    raise RuntimeError("Insufficient clearance for a safe handover.")

# Approach vertically with approximately 11 cm between the grippers.
above_receive = receive.copy()
above_receive[2] = park1[2]
p1 = translate(goto_pose_arm1, park1, above_receive, q1)
p1 = translate(goto_pose_arm1, p1, receive, q1)
close_gripper_arm1()

# Maintain support until the receiving gripper is closed.
open_gripper_arm0()
retreat = p0 + np.array([0.0, 0.0, 0.16])
p0 = translate(goto_pose_arm0, p0, retreat, q0_transfer)
retreat = p0 + np.array([-0.18, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat, q0_transfer)