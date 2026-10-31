# Code block 0
import numpy as np

q0_pick = np.array([0.0, 2**-0.5, 2**-0.5, 0.0])
q0_pass = np.array([0.0, 1.0, 0.0, 0.0])
q1_pass = np.array([0.0, 0.0, 1.0, 0.0])

hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
clearance_z = max(0.38, hammer_initial[2] + 0.22)
handover_center = np.array([0.81, 0.0, 0.175])
grasp_offset = 0.055

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

# Keep the receiving arm on its own side until the hammer is positioned.
open_gripper_arm1()
p1 = np.array([1.18, 0.0, clearance_z])
goto_pose_arm1(p1, q1_pass)

# Grip the head-side portion of the handle, leaving its other end free.
open_gripper_arm0()
pickup = hammer_initial + np.array([0.0, -grasp_offset, 0.0])
p0 = pickup.copy()
p0[2] = clearance_z
goto_pose_arm0(p0, q0_pick)
p0 = translate(goto_pose_arm0, p0, pickup, q0_pick)

close_gripper_arm0()
lifted = p0.copy()
lifted[2] = clearance_z
p0 = translate(goto_pose_arm0, p0, lifted, q0_pick)

hammer_lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if hammer_lifted[2] < hammer_initial[2] + 0.08:
    raise RuntimeError("Hammer did not lift; do not move over the gap.")

# Rotate in place above the pickup area, before translating.
# A -90 degree world-Z rotation points the free handle end toward Arm 1.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    half_angle = np.pi / 4.0 + angle / 2.0
    quaternion = np.array([
        0.0, np.cos(half_angle), np.sin(half_angle), 0.0
    ])
    goto_pose_arm0(p0, quaternion)

# Use the measured handle center rather than assuming perfect pickup alignment.
hammer_rotated = np.asarray(get_hammer_pose()[0], dtype=float)
held_offset = hammer_rotated - p0
transfer_pose = handover_center - held_offset

waypoint = p0.copy()
waypoint[1] = transfer_pose[1]
p0 = translate(goto_pose_arm0, p0, waypoint, q0_pass)

waypoint = p0.copy()
waypoint[0] = transfer_pose[0]
p0 = translate(goto_pose_arm0, p0, waypoint, q0_pass)
p0 = translate(goto_pose_arm0, p0, transfer_pose, q0_pass)

# Correct the actual hammer height while Arm 1 remains parked.
for _ in range(3):
    measured = np.asarray(get_hammer_pose()[0], dtype=float)
    error = handover_center - measured
    if np.linalg.norm(error) < 0.003:
        break
    p0 = translate(goto_pose_arm0, p0, p0 + error, q0_pass)

measured = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= measured[2] <= 0.20:
    raise RuntimeError("Hammer is outside the permitted handover height.")

# Both grasps lie on even the shortest handle, approximately 11 cm apart.
receive = measured + np.array([grasp_offset, 0.0, 0.0])
if np.linalg.norm(receive[:2] - p0[:2]) < 0.09:
    raise RuntimeError("Insufficient gripper separation for transfer.")

above_receive = receive.copy()
above_receive[2] = clearance_z
p1 = translate(goto_pose_arm1, p1, above_receive, q1_pass)
p1 = translate(goto_pose_arm1, p1, receive, q1_pass)

# Establish the receiving grasp before releasing the supporting grasp.
close_gripper_arm1()
open_gripper_arm0()

# Withdraw vertically without sweeping across the hammer or receiving gripper.
retreat = p0.copy()
retreat[2] = clearance_z
p0 = translate(goto_pose_arm0, p0, retreat, q0_pass)
retreat = p0.copy()
retreat[0] = 0.44
p0 = translate(goto_pose_arm0, p0, retreat, q0_pass)