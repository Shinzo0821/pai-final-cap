# Code block 0
import numpy as np

q0_pick = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q0_pass = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
safe_z = max(0.40, hammer[2] + 0.25)

# Keep the receiving arm on its own side throughout pickup and rotation.
receiver = np.array([1.18, 0.0, safe_z])
goto_pose_arm1(receiver, q1)
open_gripper_arm1()
open_gripper_arm0()

# Both grasp sites remain on even the shortest handle, 10 cm apart.
pickup = hammer + np.array([0.0, -0.05, 0.0])
above = pickup.copy()
above[2] = safe_z
goto_pose_arm0(above, q0_pick)
holder = translate(goto_pose_arm0, above, pickup, q0_pick)
close_gripper_arm0()

raised = holder.copy()
raised[2] = safe_z
holder = translate(goto_pose_arm0, holder, raised, q0_pick)

# Rotate in place while high and away from the receiving arm.
# The handle's +Y direction becomes +X, presenting its free end to Arm 1.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    theta = np.pi / 4.0 + angle / 2.0
    quaternion = np.array([0.0, np.cos(theta), np.sin(theta), 0.0])
    goto_pose_arm0(holder, quaternion)

# Position the actual handle midpoint, rather than assuming zero grasp offset.
center, _ = get_hammer_pose()
center = np.asarray(center, dtype=float)
destination = np.array([0.81, 0.0, 0.175])
horizontal = holder.copy()
horizontal[:2] += destination[:2] - center[:2]
holder = translate(goto_pose_arm0, holder, horizontal, q0_pass)

center, _ = get_hammer_pose()
lowered = holder.copy()
lowered[2] += destination[2] - float(center[2])
holder = translate(goto_pose_arm0, holder, lowered, q0_pass)

center, _ = get_hammer_pose()
center = np.asarray(center, dtype=float)
if not 0.15 <= center[2] <= 0.20:
    raise RuntimeError("Hammer is outside the permitted handover height.")

receive = center + np.array([0.05, 0.0, 0.0])
if np.linalg.norm(receive[:2] - holder[:2]) < 0.08:
    raise RuntimeError("Insufficient gripper separation; retaining Arm 0 grasp.")

# Approach vertically at the exposed handle end, with no concurrent motion.
above_receive = receive.copy()
above_receive[2] = safe_z
receiver = translate(goto_pose_arm1, receiver, above_receive, q1)
receiver = translate(goto_pose_arm1, receiver, receive, q1)
close_gripper_arm1()

# Establish the receiving grasp before releasing over the central gap.
open_gripper_arm0()
clear = holder.copy()
clear[2] = safe_z
holder = translate(goto_pose_arm0, holder, clear, q0_pass)
retreat = holder.copy()
retreat[0] = 0.44
translate(goto_pose_arm0, holder, retreat, q0_pass)