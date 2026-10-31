# Code block 0
import numpy as np

q0 = np.array([0.0, 1.0, 1.0, 0.0])
q0 /= np.linalg.norm(q0)
q1 = np.array([0.0, 0.0, 1.0, 0.0])

hammer_initial, _ = get_hammer_pose()
hammer_initial = np.asarray(hammer_initial, dtype=float)
safe_z = max(0.40, hammer_initial[2] + 0.25)
handover_center = np.array([0.81, 0.0, 0.175])

def translate(move, start, end, quaternion, step=0.02):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    count = max(1, int(np.ceil(np.linalg.norm(end - start) / step)))
    for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
        move(start + fraction * (end - start), quaternion)
    return end.copy()

open_gripper_arm0()
open_gripper_arm1()

# Keep the receiving arm on its own side while the hammer is collected.
receiver_park = np.array([1.18, 0.0, safe_z + 0.10])
goto_pose_arm1(receiver_park, q1)

# Grasp toward the head end of the handle, leaving its tip for Arm 1.
pickup = hammer_initial + np.array([0.0, -0.055, 0.0])
giver_position = pickup.copy()
giver_position[2] = safe_z
goto_pose_arm0(giver_position, q0)
giver_position = translate(goto_pose_arm0, giver_position, pickup, q0)
close_gripper_arm0()

raised = giver_position.copy()
raised[2] = safe_z
giver_position = translate(goto_pose_arm0, giver_position, raised, q0)

# Rotate in place above the table: the handle now points toward Arm 1 (+X).
# Separate rotation from translation to avoid sweeping the hammer at low height.
for angle in np.linspace(0.0, -np.pi / 2.0, 19)[1:]:
    c = np.cos(angle / 2.0)
    s = np.sin(angle / 2.0)
    rotated_q = np.array([
        0.0,
        c * q0[1] - s * q0[2],
        c * q0[2] + s * q0[1],
        0.0,
    ])
    goto_pose_arm0(giver_position, rotated_q)

q0 = rotated_q

# Measure the handle center rather than trusting the reported orientation.
hammer_now, _ = get_hammer_pose()
hammer_now = np.asarray(hammer_now, dtype=float)
giver_target = giver_position + handover_center - hammer_now
giver_above = giver_target.copy()
giver_above[2] = safe_z

giver_position = translate(
    goto_pose_arm0, giver_position, giver_above, q0
)
giver_position = translate(
    goto_pose_arm0, giver_position, giver_target, q0
)

# Correct any residual positional error while Arm 0 retains the hammer.
for _ in range(2):
    hammer_now, _ = get_hammer_pose()
    error = handover_center - np.asarray(hammer_now, dtype=float)
    if np.linalg.norm(error) < 0.003:
        break
    giver_position = translate(
        goto_pose_arm0, giver_position, giver_position + error, q0,
        step=0.01,
    )

hammer_now, _ = get_hammer_pose()
hammer_now = np.asarray(hammer_now, dtype=float)
if not 0.15 <= hammer_now[2] <= 0.20:
    raise RuntimeError("Hammer is outside the permitted handover height.")

# Opposite handle grasp sites are 11 cm apart, exceeding the 8 cm buffer.
receiver_target = hammer_now + np.array([0.055, 0.0, 0.0])
if np.linalg.norm(receiver_target[:2] - giver_position[:2]) < 0.08:
    raise RuntimeError("Insufficient clearance between grippers.")

receiver_above = receiver_target.copy()
receiver_above[2] = safe_z + 0.10
receiver_position = translate(
    goto_pose_arm1, receiver_park, receiver_above, q1
)
receiver_position = translate(
    goto_pose_arm1, receiver_position, receiver_target, q1,
    step=0.01,
)
close_gripper_arm1()

# Never release the giver until the receiver has closed around the handle.
open_gripper_arm0()

giver_retreat = giver_position + np.array([0.0, 0.0, 0.15])
giver_position = translate(
    goto_pose_arm0, giver_position, giver_retreat, q0,
    step=0.01,
)