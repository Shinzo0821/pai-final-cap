# Code block 0
import numpy as np

q0_pick = np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0)
q0_pass = np.array([0.0, 1.0, 0.0, 0.0])
q1 = np.array([0.0, 0.0, 1.0, 0.0])

def move_steps(move, start, end, quaternion, step=0.025):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

handle, _ = get_hammer_pose()
handle = np.asarray(handle, dtype=float)
safe_z = max(0.35, float(handle[2]) + 0.20)

open_gripper_arm1()
receiver_park = np.array([1.18, 0.0, safe_z])
goto_pose_arm1(receiver_park, q1)

# Leave more than 10 cm of handle between the two grasp locations.
open_gripper_arm0()
pickup = handle + np.array([0.0, -0.045, 0.0])
above_pickup = pickup.copy()
above_pickup[2] = safe_z
goto_pose_arm0(above_pickup, q0_pick)
p0 = move_steps(goto_pose_arm0, above_pickup, pickup, q0_pick)
close_gripper_arm0()

lifted = p0.copy()
lifted[2] = safe_z
p0 = move_steps(goto_pose_arm0, p0, lifted, q0_pick)

# Rotate only after lifting: the handle's free end now points toward Arm 1.
for angle in np.linspace(0.0, np.pi / 2.0, 13)[1:]:
    half_angle = np.pi / 4.0 - angle / 2.0
    quaternion = np.array([
        0.0, np.cos(half_angle), np.sin(half_angle), 0.0
    ])
    goto_pose_arm0(p0, quaternion)

# Translate at clearance height before lowering into the handover region.
measured, _ = get_hammer_pose()
measured = np.asarray(measured, dtype=float)
target_handle = np.array([0.81, 0.0, 0.175])
high_target = target_handle.copy()
high_target[2] = measured[2]
p0 = move_steps(
    goto_pose_arm0, p0, p0 + high_target - measured, q0_pass
)

measured, _ = get_hammer_pose()
measured = np.asarray(measured, dtype=float)
p0 = move_steps(
    goto_pose_arm0, p0, p0 + target_handle - measured, q0_pass
)

# Approach the opposite end of the handle from above.
# The grippers remain 10.5 cm apart even at equal height.
receiver_grasp = p0 + np.array([0.105, 0.0, 0.0])
receiver_above = receiver_grasp.copy()
receiver_above[2] = safe_z
p1 = move_steps(
    goto_pose_arm1, receiver_park, receiver_above, q1
)
p1 = move_steps(goto_pose_arm1, p1, receiver_grasp, q1)
close_gripper_arm1()

# Transfer support before withdrawing the donor.
open_gripper_arm0()
donor_above = p0 + np.array([0.0, 0.0, 0.15])
p0 = move_steps(goto_pose_arm0, p0, donor_above, q0_pass)
move_steps(
    goto_pose_arm0, p0, p0 + np.array([-0.15, 0.0, 0.0]), q0_pass
)