# Code block 0
import numpy as np

q0_down = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5), 0.0])
q1_down = np.array([0.0, 0.0, 1.0, 0.0])

def translate(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        move(start + (end - start) * (i / count), quaternion)
    return end.copy()

open_gripper_arm1()
p1 = np.array([1.18, 0.0, 0.45])
goto_pose_arm1(p1, q1_down)

hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)

# Leave the distal handle free; ignore the unreliable object quaternion.
grasp_offset = 0.055
p0 = hammer + np.array([0.0, -grasp_offset, 0.0])
clearance = max(0.35, float(hammer[2]) + 0.20)

open_gripper_arm0()
above = p0.copy()
above[2] = clearance
goto_pose_arm0(above, q0_down)
p0 = translate(goto_pose_arm0, above, p0, q0_down)
close_gripper_arm0()

raised = p0.copy()
raised[2] = clearance
p0 = translate(goto_pose_arm0, p0, raised, q0_down)

# Rotate in place above the table: the handle now points toward Arm 1
# along +X, with the hammer head on Arm 0's side.
for angle in np.linspace(0.0, -np.pi / 2.0, 13)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    q0 = np.array([
        0.0,
        (c - s) / np.sqrt(2.0),
        (c + s) / np.sqrt(2.0),
        0.0,
    ])
    goto_pose_arm0(p0, q0)

q0 = np.array([0.0, 1.0, 0.0, 0.0])

# Translate at clearance before lowering into the handover region.
hammer, _ = get_hammer_pose()
hammer = np.asarray(hammer, dtype=float)
target = p0 + np.array([0.81 - hammer[0], -hammer[1], 0.0])
p0 = translate(goto_pose_arm0, p0, target, q0)

hammer, _ = get_hammer_pose()
target = p0.copy()
target[2] += 0.175 - float(hammer[2])
p0 = translate(goto_pose_arm0, p0, target, q0, step=0.015)

# Grasp the opposite portion of the handle, keeping gripper centers
# 11 cm apart. Approach vertically without sweeping across Arm 0.
hammer, _ = get_hammer_pose()
receive = np.asarray(hammer, dtype=float) + np.array([grasp_offset, 0.0, 0.0])
above_receive = receive.copy()
above_receive[2] = max(0.40, receive[2] + 0.20)

p1 = translate(goto_pose_arm1, p1, above_receive, q1_down)
p1 = translate(goto_pose_arm1, p1, receive, q1_down, step=0.015)
close_gripper_arm1()

# Keep Arm 1 fixed at the successful handover height before releasing.
open_gripper_arm0()
retreat = p0.copy()
retreat[2] += 0.18
p0 = translate(goto_pose_arm0, p0, retreat, q0)

retreat = p0.copy()
retreat[0] = 0.44
translate(goto_pose_arm0, p0, retreat, q0)