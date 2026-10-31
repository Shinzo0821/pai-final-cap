# Code block 0
import numpy as np

def unit(q):
    q = np.asarray(q, dtype=float)
    return q / np.linalg.norm(q)

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quaternion)
    return end.copy()

q0_pick = unit([0.0, 1.0, 1.0, 0.0])
q1_receive = unit([0.0, 0.0, 1.0, 0.0])

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

# Use two handle locations 11 cm apart, both inside the shortest handle.
grip_offset = 0.055
pickup = hammer + np.array([0.0, -grip_offset, 0.0])
clearance_z = max(0.35, float(hammer[2]) + 0.18)

open_gripper_arm1()
goto_pose_arm1(np.array([1.18, 0.0, clearance_z + 0.10]), q1_receive)

open_gripper_arm0()
overhead = pickup.copy()
overhead[2] = clearance_z
goto_pose_arm0(overhead, q0_pick)
p0 = translate(goto_pose_arm0, overhead, pickup, q0_pick)
close_gripper_arm0()

p0 = translate(goto_pose_arm0, p0, overhead, q0_pick)

# Rotate in place above the table: handle +Y becomes +X.
# Arm 0 retains the head-side handle section; Arm 1 takes the tip-side section.
for angle in np.linspace(0.0, -np.pi / 2.0, 13)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    a, b = q0_pick[1], q0_pick[2]
    q0_transfer = unit([0.0, c * a - s * b, c * b + s * a, 0.0])
    goto_pose_arm0(p0, q0_transfer)

# The hammer midpoint is at x=0.81 during transfer.
handover_center = np.array([0.81, 0.0, 0.175])
giver_target = handover_center + np.array([-grip_offset, 0.0, 0.0])
receiver_target = handover_center + np.array([grip_offset, 0.0, 0.0])

waypoint = p0.copy()
waypoint[0] = giver_target[0]
p0 = translate(goto_pose_arm0, p0, waypoint, q0_transfer)

waypoint = p0.copy()
waypoint[1] = giver_target[1]
p0 = translate(goto_pose_arm0, p0, waypoint, q0_transfer)
p0 = translate(goto_pose_arm0, p0, giver_target, q0_transfer)

# Correct for any small shift of the hammer within the giver's grasp.
actual_center, _ = get_hammer_pose()
actual_center = np.asarray(actual_center, dtype=float)
correction = handover_center - actual_center
p0 = translate(goto_pose_arm0, p0, p0 + correction, q0_transfer)

# Approach vertically, maintaining 11 cm separation between grasp centers.
p1 = np.array([1.18, 0.0, clearance_z + 0.10])
receiver_above = receiver_target.copy()
receiver_above[2] = clearance_z + 0.10
p1 = translate(goto_pose_arm1, p1, receiver_above, q1_receive)
p1 = translate(goto_pose_arm1, p1, receiver_target, q1_receive)

# Establish the receiving grasp before releasing support over the gap.
close_gripper_arm1()
open_gripper_arm0()

giver_above = p0 + np.array([0.0, 0.0, 0.13])
p0 = translate(goto_pose_arm0, p0, giver_above, q0_transfer)
giver_retreat = p0.copy()
giver_retreat[0] = 0.44
translate(goto_pose_arm0, p0, giver_retreat, q0_transfer)