# Code block 0
import numpy as np

q0 = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q1 = np.array([0.0, 0.0, 1.0, 0.0])
q_transfer = np.array([0.0, 1.0, 0.0, 0.0])

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quaternion)
    return end.copy()

hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
clearance = max(0.40, hammer_initial[2] + 0.22)

# Park the receiving arm outside the transfer corridor.
open_gripper_arm1()
p1 = np.array([1.18, 0.0, clearance + 0.10])
goto_pose_arm1(p1, q1)

# Both grasp points remain on even the shortest handle.
# Their 10 cm separation exceeds the required 8 cm buffer.
open_gripper_arm0()
grasp0 = hammer_initial + np.array([0.0, -0.05, 0.0])
p0 = grasp0.copy()
p0[2] = clearance
goto_pose_arm0(p0, q0)
p0 = translate(goto_pose_arm0, p0, grasp0, q0, step=0.01)
close_gripper_arm0()

lift = p0.copy()
lift[2] = clearance
p0 = translate(goto_pose_arm0, p0, lift, q0)

hammer_lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if hammer_lifted[2] < hammer_initial[2] + 0.08:
    raise RuntimeError("Hammer did not lift; refusing to cross the table gap.")

# Rotate in place, clear of the table: handle +Y becomes +X.
# The head stays toward Arm 0; the free handle end faces Arm 1.
for angle in np.linspace(0.0, np.pi / 2.0, 19)[1:]:
    half = np.pi / 4.0 - angle / 2.0
    quaternion = np.array([0.0, np.cos(half), np.sin(half), 0.0])
    goto_pose_arm0(p0, quaternion)

# Use the measured handle center rather than its unreliable quaternion.
hammer_rotated = np.asarray(get_hammer_pose()[0], dtype=float)
offset = hammer_rotated - p0
handover_center = np.array([0.81, 0.0, 0.175])
transfer0 = handover_center - offset

waypoint = p0.copy()
waypoint[1] = transfer0[1]
p0 = translate(goto_pose_arm0, p0, waypoint, q_transfer)
waypoint[0] = transfer0[0]
p0 = translate(goto_pose_arm0, p0, waypoint, q_transfer)
p0 = translate(goto_pose_arm0, p0, transfer0, q_transfer, step=0.01)

hammer_now = np.asarray(get_hammer_pose()[0], dtype=float)
correction = handover_center - hammer_now
p0 = translate(goto_pose_arm0, p0, p0 + correction, q_transfer, step=0.005)

hammer_now = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= hammer_now[2] <= 0.20:
    raise RuntimeError("Hammer is outside the required handover height.")

receive = hammer_now + np.array([0.05, 0.0, 0.0])
if np.linalg.norm(receive[:2] - p0[:2]) < 0.085:
    raise RuntimeError("Insufficient gripper clearance for handover.")

# Approach from above without sweeping through the holding gripper.
waypoint1 = p1.copy()
waypoint1[1] = receive[1]
p1 = translate(goto_pose_arm1, p1, waypoint1, q1)
waypoint1[0] = receive[0]
p1 = translate(goto_pose_arm1, p1, waypoint1, q1)
p1 = translate(goto_pose_arm1, p1, receive, q1, step=0.01)

# Establish the receiving grasp before releasing over the gap.
close_gripper_arm1()
open_gripper_arm0()

retreat0 = p0 + np.array([0.0, 0.0, 0.16])
p0 = translate(goto_pose_arm0, p0, retreat0, q_transfer, step=0.01)
retreat0 = p0 + np.array([-0.15, 0.0, 0.0])
p0 = translate(goto_pose_arm0, p0, retreat0, q_transfer)