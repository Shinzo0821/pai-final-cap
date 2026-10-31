# Code block 0
import numpy as np

q_pick = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q_give = np.array([0.0, 1.0, 0.0, 0.0])
q_receive = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * i / count, quaternion)
    return end.copy()

hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
safe_z = max(0.40, hammer_initial[2] + 0.23)

# Keep the receiving arm well outside the pickup and rotation region.
open_gripper_arm1()
receiver_park = np.array([1.18, 0.0, safe_z])
goto_pose_arm1(receiver_park, q_receive)

# Two handle grasps 10 cm apart fit even the shortest handle.
# Arm 0 takes the headward portion, leaving the tipward portion free.
open_gripper_arm0()
pickup = hammer_initial + np.array([0.0, -0.05, 0.0])
above_pickup = pickup.copy()
above_pickup[2] = safe_z
goto_pose_arm0(above_pickup, q_pick)
p0 = translate(goto_pose_arm0, above_pickup, pickup, q_pick)
close_gripper_arm0()

lifted = pickup.copy()
lifted[2] = safe_z
p0 = translate(goto_pose_arm0, p0, lifted, q_pick)

hammer_lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if np.linalg.norm((hammer_lifted - hammer_initial) - (lifted - pickup)) > 0.025:
    raise RuntimeError("Pickup was not confirmed; do not enter the central gap.")

# Rotate in place above the table: the handle now points toward Arm 1,
# while the hammer head stays on Arm 0's side of the transfer.
for angle in np.linspace(np.pi / 4.0, 0.0, 13)[1:]:
    q = np.array([0.0, np.cos(angle), np.sin(angle), 0.0])
    goto_pose_arm0(p0, q)

hammer_rotated = np.asarray(get_hammer_pose()[0], dtype=float)
handle_offset = hammer_rotated - p0
handover_center = np.array([(0.44 + 1.18) / 2.0, 0.0, 0.175])
transfer_grasp = handover_center - handle_offset

high_transfer = transfer_grasp.copy()
high_transfer[2] = safe_z
p0 = translate(goto_pose_arm0, p0, high_transfer, q_give)
p0 = translate(goto_pose_arm0, p0, transfer_grasp, q_give)

hammer_transfer = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= hammer_transfer[2] <= 0.20:
    raise RuntimeError("Hammer is outside the permitted handover height.")

receiver_grasp = hammer_transfer + np.array([0.05, 0.0, 0.0])
if np.linalg.norm(receiver_grasp - p0) < 0.09:
    raise RuntimeError("Insufficient gripper clearance for transfer.")

# Approach vertically with jaws crossing the handle, not the hammer head.
above_receive = receiver_grasp.copy()
above_receive[2] = safe_z
p1 = translate(goto_pose_arm1, receiver_park, above_receive, q_receive)
p1 = translate(goto_pose_arm1, p1, receiver_grasp, q_receive)
close_gripper_arm1()

# Establish the receiving grasp before relinquishing support over the gap.
open_gripper_arm0()
retreat0 = p0.copy()
retreat0[2] = safe_z
p0 = translate(goto_pose_arm0, p0, retreat0, q_give)
retreat0 = p0.copy()
retreat0[0] = 0.44
translate(goto_pose_arm0, p0, retreat0, q_give)