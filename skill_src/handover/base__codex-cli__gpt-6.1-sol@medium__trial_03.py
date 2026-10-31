# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

handover_center = np.array([(0.44 + 1.18) / 2.0, 0.0, 0.175])
clearance_z = max(0.35, hammer[2] + 0.22)

open_gripper_arm1()
park1 = np.array([1.18, 0.0, clearance_z])
goto_pose_arm1(park1, q1)

# Grip the head-side portion of the handle, leaving its distal end free.
open_gripper_arm0()
pickup = hammer + np.array([0.0, -0.05, 0.0])
above_pickup = pickup.copy()
above_pickup[2] = clearance_z
goto_pose_arm0(above_pickup, q0_pick)
p0 = translate(goto_pose_arm0, above_pickup, pickup, q0_pick)
close_gripper_arm0()

lifted = pickup.copy()
lifted[2] = clearance_z
p0 = translate(goto_pose_arm0, p0, lifted, q0_pick)

# Rotate in place while clear of the table: the handle now points toward +X.
for angle in np.linspace(0.0, -np.pi / 2.0, 13)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    quaternion = np.array([0.0, (c - s) / np.sqrt(2.0),
                           (c + s) / np.sqrt(2.0), 0.0])
    goto_pose_arm0(p0, quaternion)

# Measure the actual handle-center offset after lifting and rotating.
held_center, _ = get_hammer_pose()
offset = np.asarray(held_center, dtype=float) - p0
transfer0 = handover_center - offset

waypoint = p0.copy()
waypoint[1] = transfer0[1]
p0 = translate(goto_pose_arm0, p0, waypoint, q0_transfer)
waypoint = p0.copy()
waypoint[0] = transfer0[0]
p0 = translate(goto_pose_arm0, p0, waypoint, q0_transfer)
p0 = translate(goto_pose_arm0, p0, transfer0, q0_transfer)

# Correct the hammer height before bringing the receiving arm close.
actual_center, _ = get_hammer_pose()
correction = handover_center - np.asarray(actual_center, dtype=float)
p0 = translate(goto_pose_arm0, p0, p0 + correction, q0_transfer)

actual_center, _ = get_hammer_pose()
actual_center = np.asarray(actual_center, dtype=float)
receive = actual_center + np.array([0.05, 0.0, 0.0])

if not 0.15 <= actual_center[2] <= 0.20:
    raise RuntimeError("Hammer is outside the handover height range.")
if np.linalg.norm(receive[:2] - p0[:2]) < 0.08:
    raise RuntimeError("Insufficient gripper separation for a safe handover.")

# Approach vertically; both grippers remain approximately 10 cm apart.
above_receive = receive.copy()
above_receive[2] = clearance_z
p1 = translate(goto_pose_arm1, park1, above_receive, q1)
p1 = translate(goto_pose_arm1, p1, receive, q1)
close_gripper_arm1()

# Maintain support until the receiving gripper has closed.
open_gripper_arm0()
retreat0 = p0.copy()
retreat0[2] = clearance_z
p0 = translate(goto_pose_arm0, p0, retreat0, q0_transfer)
retreat0 = p0.copy()
retreat0[0] = 0.44
translate(goto_pose_arm0, p0, retreat0, q0_transfer)