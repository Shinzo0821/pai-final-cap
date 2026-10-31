# Code block 0
import numpy as np

q0_pick = np.array([0.0, 2**-0.5, 2**-0.5, 0.0])
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
clearance = max(0.38, hammer[2] + 0.20)

# Keep the receiving arm outside the transfer corridor.
open_gripper_arm1()
p1 = np.array([1.18, 0.0, clearance])
goto_pose_arm1(p1, q1)

open_gripper_arm0()
p0 = np.array([0.44, 0.0, clearance])
goto_pose_arm0(p0, q0_pick)

# Both grip sites fit within even the shortest handle.
# Arm 0 holds toward the head; Arm 1 receives toward the free end.
offset = 0.055
pickup = hammer + np.array([0.0, -offset, 0.0])
above = pickup.copy()
above[2] = clearance
p0 = translate(goto_pose_arm0, p0, above, q0_pick)
p0 = translate(goto_pose_arm0, p0, pickup, q0_pick, 0.01)
close_gripper_arm0()

p0 = translate(goto_pose_arm0, p0, above, q0_pick, 0.015)

# Rotate in place above the table: handle +Y becomes +X.
# This places the receiver on its own side with 11 cm grip separation.
for angle in np.linspace(np.pi / 4.0, 0.0, 13)[1:]:
    quaternion = np.array([0.0, np.cos(angle), np.sin(angle), 0.0])
    goto_pose_arm0(p0, quaternion)

observed, _ = get_hammer_pose()
observed = np.asarray(observed, dtype=float)
target = np.array([0.81, 0.0, 0.175])

high_target = target.copy()
high_target[2] = clearance
p0 = translate(
    goto_pose_arm0, p0, p0 + high_target - observed, q0_pass
)

observed, _ = get_hammer_pose()
p0 = translate(
    goto_pose_arm0,
    p0,
    p0 + target - np.asarray(observed, dtype=float),
    q0_pass,
    0.01,
)

# Correct using the measured handle center rather than gripper height.
for _ in range(3):
    observed, _ = get_hammer_pose()
    observed = np.asarray(observed, dtype=float)
    if np.linalg.norm(target - observed) < 0.003:
        break
    p0 = translate(
        goto_pose_arm0, p0, p0 + target - observed, q0_pass, 0.005
    )

observed, _ = get_hammer_pose()
observed = np.asarray(observed, dtype=float)
if not 0.15 <= observed[2] <= 0.20:
    raise RuntimeError("Hammer is outside the handover height range.")

receive = observed + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receive[:2] - p0[:2]) < 0.09:
    raise RuntimeError("Insufficient gripper separation for handover.")

above_receive = receive.copy()
above_receive[2] = clearance
p1 = translate(goto_pose_arm1, p1, above_receive, q1)
p1 = translate(goto_pose_arm1, p1, receive, q1, 0.01)

# Establish the receiving grasp before releasing support over the gap.
close_gripper_arm1()
open_gripper_arm0()

retreat = p0.copy()
retreat[2] = clearance
p0 = translate(goto_pose_arm0, p0, retreat, q0_pass, 0.01)
p0 = translate(
    goto_pose_arm0, p0, np.array([0.44, 0.0, clearance]), q0_pass
)