# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, finish, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    finish = np.asarray(finish, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(finish - start) / step)))
    for i in range(1, count + 1):
        move(start + (finish - start) * i / count, quaternion)
    return finish.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
clear_z = max(0.36, hammer[2] + 0.22)

# Park the receiving arm on its own side before approaching the hammer.
open_gripper_arm1()
p1 = np.array([1.18, 0.0, clear_z])
goto_pose_arm1(p1, q1)

open_gripper_arm0()
p0 = np.array([0.44, 0.0, clear_z])
goto_pose_arm0(p0, q0_pick)

# Both grasp sites remain on even the shortest handle, separated by 11 cm.
offset = 0.055
pickup = hammer + np.array([0.0, -offset, 0.0])
above_pickup = pickup.copy()
above_pickup[2] = clear_z
p0 = translate(goto_pose_arm0, p0, above_pickup, q0_pick)
p0 = translate(goto_pose_arm0, p0, pickup, q0_pick, step=0.01)
close_gripper_arm0()
p0 = translate(goto_pose_arm0, p0, above_pickup, q0_pick)

# Rotate only while elevated: the handle now points toward Arm 1 (+X).
# Keep the grasp position fixed throughout this rotation.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    q = np.array([0.0, (c - s) / np.sqrt(2.0),
                  (c + s) / np.sqrt(2.0), 0.0])
    goto_pose_arm0(p0, q)

handover_center = np.array([0.81, 0.0, 0.175])
giver_target = handover_center - np.array([offset, 0.0, 0.0])
giver_high = giver_target.copy()
giver_high[2] = clear_z

p0 = translate(goto_pose_arm0, p0, giver_high, q0_transfer)
p0 = translate(goto_pose_arm0, p0, giver_target, q0_transfer, step=0.01)

# Correct residual object displacement before bringing the receiver close.
actual_center, _ = get_hammer_pose()
correction = handover_center - np.asarray(actual_center, dtype=float)
p0 = translate(goto_pose_arm0, p0, p0 + correction,
               q0_transfer, step=0.01)

actual_center, _ = get_hammer_pose()
actual_center = np.asarray(actual_center, dtype=float)
receiver_target = actual_center + np.array([offset, 0.0, 0.0])
receiver_high = receiver_target.copy()
receiver_high[2] = clear_z

p1 = translate(goto_pose_arm1, p1, receiver_high, q1)
p1 = translate(goto_pose_arm1, p1, receiver_target, q1, step=0.01)

# Establish the receiving grasp before releasing the supporting grasp.
close_gripper_arm1()
open_gripper_arm0()

# Withdraw vertically first, maintaining more than 8 cm gripper clearance.
giver_retreat = p0.copy()
giver_retreat[2] = clear_z
p0 = translate(goto_pose_arm0, p0, giver_retreat, q0_transfer)
p0 = translate(goto_pose_arm0, p0,
               np.array([0.44, 0.0, clear_z]), q0_transfer)