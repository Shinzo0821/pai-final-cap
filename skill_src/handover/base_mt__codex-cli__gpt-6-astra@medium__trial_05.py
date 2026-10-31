# Code block 0
import numpy as np

def unit(q):
    q = np.asarray(q, dtype=float)
    return q / np.linalg.norm(q)

q0_initial = unit([0, 1, 1, 0])
q1 = unit([0, 0, 1, 0])
hammer_initial = np.asarray(get_hammer_pose()[0], dtype=float).copy()
height = max(0.38, hammer_initial[2] + 0.22)
offset = 0.055
handover = np.array([0.81, 0.0, 0.175])

def translate(api, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for i in range(1, count + 1):
        api(start + (end - start) * (i / count), quaternion)
    return end.copy()

# Keep the receiving arm outside the donor's working region.
open_gripper_arm1()
receiver = np.array([1.18, 0.0, height + 0.12])
goto_pose_arm1(receiver, q1)

# Grasp the head-side portion of the handle, leaving its other end free.
open_gripper_arm0()
pickup = hammer_initial + np.array([0.0, -offset, 0.0])
donor = pickup.copy()
donor[2] = height
goto_pose_arm0(donor, q0_initial)
donor = translate(goto_pose_arm0, donor, pickup, q0_initial)
close_gripper_arm0()

donor = translate(
    goto_pose_arm0, donor,
    pickup + np.array([0.0, 0.0, 0.07]), q0_initial
)
lifted = np.asarray(get_hammer_pose()[0], dtype=float)
if lifted[2] - hammer_initial[2] < 0.04:
    raise RuntimeError("Hammer did not follow the pickup; aborting before the gap.")

raised = donor.copy()
raised[2] = height
donor = translate(goto_pose_arm0, donor, raised, q0_initial)

# Rotate in place above the table: +Y handle direction becomes +X.
# Thus each arm grasps its own side of the hammer, without crossing.
for angle in np.linspace(0.0, -np.pi / 2.0, 13)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    q0 = unit([0.0, (c - s) / np.sqrt(2.0),
               (c + s) / np.sqrt(2.0), 0.0])
    goto_pose_arm0(donor, q0)

# Preserve the measured grasp offset rather than assuming a perfect pickup.
hammer = np.asarray(get_hammer_pose()[0], dtype=float)
overhead_center = handover.copy()
overhead_center[2] = max(height, hammer[2])
target = donor + overhead_center - hammer

vertical = donor.copy()
vertical[2] = target[2]
donor = translate(goto_pose_arm0, donor, vertical, q0)
donor = translate(goto_pose_arm0, donor, target, q0)

hammer = np.asarray(get_hammer_pose()[0], dtype=float)
target = donor + handover - hammer
donor = translate(goto_pose_arm0, donor, target, q0)

hammer = np.asarray(get_hammer_pose()[0], dtype=float)
if not 0.15 <= hammer[2] <= 0.20:
    raise RuntimeError("Hammer is outside the required handover height.")

receive = hammer + np.array([offset, 0.0, 0.0])
if np.linalg.norm(receive[:2] - donor[:2]) < 0.09:
    raise RuntimeError("Insufficient clearance between grippers.")

# Approach vertically with fingers closing across, not along, the handle.
above_receive = receive.copy()
above_receive[2] = receiver[2]
receiver = translate(goto_pose_arm1, receiver, above_receive, q1)
receiver = translate(goto_pose_arm1, receiver, receive, q1)
close_gripper_arm1()

# Establish the receiving grasp before releasing the donor.
open_gripper_arm0()
retreat = donor + np.array([0.0, 0.0, 0.15])
donor = translate(goto_pose_arm0, donor, retreat, q0)
retreat = donor + np.array([-0.15, 0.0, 0.0])
donor = translate(goto_pose_arm0, donor, retreat, q0)