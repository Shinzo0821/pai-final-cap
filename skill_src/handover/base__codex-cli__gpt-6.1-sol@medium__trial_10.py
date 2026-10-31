# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q0_transfer = np.array([0.0, 1.0, 0.0, 0.0])
q1_transfer = np.array([0.0, 0.0, 1.0, 0.0])

def translate(goto, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        goto(start + (end - start) * i / count, quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

# Grasp opposite ends of even the shortest handle, keeping 11 cm separation.
offset = 0.055
handover_center = np.array([(0.44 + 1.18) / 2.0, 0.0, 0.175])
safe_z = max(float(hammer[2]) + 0.25, 0.40)

open_gripper_arm1()
receiver_park = np.array([1.18, 0.0, safe_z])
goto_pose_arm1(receiver_park, q1_transfer)

open_gripper_arm0()
pickup = hammer + np.array([0.0, -offset, 0.0])
above_pickup = pickup.copy()
above_pickup[2] = safe_z
goto_pose_arm0(above_pickup, q0_pick)
translate(goto_pose_arm0, above_pickup, pickup, q0_pick)
close_gripper_arm0()
holder = translate(goto_pose_arm0, pickup, above_pickup, q0_pick)

# Rotate only after lifting: handle points toward +X, toward the receiver.
# Keep translation fixed throughout this rotation.
for theta in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    quaternion = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(holder, quaternion)

holder_high = handover_center + np.array([-offset, 0.0, 0.0])
holder_high[2] = safe_z
holder = translate(goto_pose_arm0, holder, holder_high, q0_transfer)

# Use measured handle height to place the hammer itself at the target height.
measured_hammer, _ = get_hammer_pose()
holder_low = holder.copy()
holder_low[2] += handover_center[2] - float(measured_hammer[2])
holder = translate(goto_pose_arm0, holder, holder_low, q0_transfer)

measured_hammer, _ = get_hammer_pose()
receiver_target = np.asarray(measured_hammer, dtype=float) + np.array([offset, 0.0, 0.0])
receiver_high = receiver_target.copy()
receiver_high[2] = max(safe_z, receiver_target[2] + 0.20)

receiver = translate(
    goto_pose_arm1, receiver_park, receiver_high, q1_transfer
)
receiver = translate(
    goto_pose_arm1, receiver, receiver_target, q1_transfer
)

# Establish the receiving grasp before releasing over the central gap.
close_gripper_arm1()
open_gripper_arm0()

# Withdraw the donor vertically while the receiver holds the hammer still.
holder_retreat = holder.copy()
holder_retreat[2] += 0.20
translate(goto_pose_arm0, holder, holder_retreat, q0_transfer)