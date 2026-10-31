# Code block 0
# Read the poses and bounding box extents of both cubes
red_pos, red_quat, red_ext = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_ext = get_object_pose("green cube", return_bbox_extent=True)

# Assume returned positions are object centers. The top surface of the green cube is center z + half its height.
green_top_z = green_pos[2] + green_ext[2] / 2.0
red_half_h = red_ext[2] / 2.0

# Target z for the red cube center so its bottom rests on the green cube's top face.
# A small 2 mm clearance avoids collision during the final descent.
clearance = 0.002
target_red_center_z = green_top_z + red_half_h + clearance

# Sample a grasp pose for the red cube and use its quaternion for the gripper orientation.
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Offset from the red cube center to the end-effector grasp point.
# Reusing this offset keeps the cube centered over the green cube at placement.
grasp_offset = grasp_pos - red_pos

# Pick the red cube
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)  # approach from directly above
close_gripper()

# Lift the cube straight up before traveling
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.12])
goto_pose(lift_pos, grasp_quat)

# Compute the end-effector placement pose so the red cube center lands at the target.
green_xy = green_pos[:2]
place_pos = np.array([
    green_xy[0] + grasp_offset[0],
    green_xy[1] + grasp_offset[1],
    target_red_center_z + grasp_offset[2],
])

# Move above the green cube, then descend slowly to the placement pose.
hover_pos = place_pos + np.array([0.0, 0.0, 0.08])
goto_pose(hover_pos, grasp_quat)
goto_pose(place_pos, grasp_quat)

# Release the cube at the computed height, which keeps the drop distance minimal
open_gripper()

# Retreat straight up so the gripper does not disturb the placed cube
retreat_pos = place_pos + np.array([0.0, 0.0, 0.10])
goto_pose(retreat_pos, grasp_quat)

# Code block 1
import numpy as np

# Read the poses and bounding box extents of both cubes
red_pos, red_quat, red_ext = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_ext = get_object_pose("green cube", return_bbox_extent=True)

# Top surface of the green cube = its center z + half its height
green_top_z = green_pos[2] + green_ext[2] / 2.0
red_half_h = red_ext[2] / 2.0

# Target z for the red cube center so its bottom rests on the green cube's top face.
# A 2 mm clearance avoids collision during the final descent.
clearance = 0.002
target_red_center_z = green_top_z + red_half_h + clearance

# Sample a grasp pose for the red cube and use its quaternion for gripper orientation
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Offset from the red cube center to the end-effector grasp point
grasp_offset = grasp_pos - red_pos

# Pick the red cube
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)  # approach from directly above
close_gripper()

# Lift the cube straight up before traveling
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.12])
goto_pose(lift_pos, grasp_quat)

# End-effector placement pose so the red cube center lands at the target
green_xy = green_pos[:2]
place_pos = np.array([
    green_xy[0] + grasp_offset[0],
    green_xy[1] + grasp_offset[1],
    target_red_center_z + grasp_offset[2],
])

# Move above the green cube, then descend slowly to the placement pose
hover_pos = place_pos + np.array([0.0, 0.0, 0.08])
goto_pose(hover_pos, grasp_quat)
goto_pose(place_pos, grasp_quat)

# Release the cube at the computed height
open_gripper()

# Retreat straight up so the gripper does not disturb the placed cube
retreat_pos = place_pos + np.array([0.0, 0.0, 0.10])
goto_pose(retreat_pos, grasp_quat)

# Report final cube positions for verification
final_red_pos, _, _ = get_object_pose("red cube", return_bbox_extent=True)
final_green_pos, _, _ = get_object_pose("green cube", return_bbox_extent=True)
print("red cube final position:", final_red_pos)
print("green cube final position:", final_green_pos)

# Code block 2
import numpy as np

# Read current poses and bounding box extents of both cubes
red_pos, red_quat, red_ext = get_object_pose("red cube", return_bbox_extent=True)
green_pos, green_quat, green_ext = get_object_pose("green cube", return_bbox_extent=True)

# Green cube top surface = center z + half its height
green_top_z = green_pos[2] + green_ext[2] / 2.0
red_half_h = red_ext[2] / 2.0

# Target red cube center z: bottom of red rests on top of green, with small clearance
clearance = 0.003
target_red_center_z = green_top_z + red_half_h + clearance

# Sample a grasp pose for the red cube and use its quaternion for gripper orientation
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Offset from red cube center to the grasp point (end-effector frame relative to cube center)
grasp_offset = grasp_pos - red_pos

# Pick the red cube from directly above
open_gripper()
goto_pose(grasp_pos, grasp_quat, z_approach=0.10)
close_gripper()

# Lift straight up before traveling
lift_pos = grasp_pos + np.array([0.0, 0.0, 0.15])
goto_pose(lift_pos, grasp_quat)

# End-effector pose so the red cube center lands above the green cube center at target height
green_xy = green_pos[:2]
place_pos = np.array([
    green_xy[0] + grasp_offset[0],
    green_xy[1] + grasp_offset[1],
    target_red_center_z + grasp_offset[2],
])

# Move above the green cube, then descend in two stages to keep the drop height minimal
hover_pos = place_pos + np.array([0.0, 0.0, 0.10])
goto_pose(hover_pos, grasp_quat)

near_pos = place_pos + np.array([0.0, 0.0, 0.02])
goto_pose(near_pos, grasp_quat)
goto_pose(place_pos, grasp_quat)

# Release the cube at the computed height
open_gripper()

# Retreat straight up so the gripper does not disturb the placed cube
retreat_pos = place_pos + np.array([0.0, 0.0, 0.12])
goto_pose(retreat_pos, grasp_quat)

# Verify final cube positions
final_red_pos, _, _ = get_object_pose("red cube", return_bbox_extent=True)
final_green_pos, _, final_green_ext = get_object_pose("green cube", return_bbox_extent=True)
print("red cube final position:", final_red_pos)
print("green cube final position:", final_green_pos)
print("target red center z:", target_red_center_z)

expected_red_z = final_green_pos[2] + final_green_ext[2] / 2.0 + red_half_h
xy_error = np.linalg.norm(final_red_pos[:2] - final_green_pos[:2])
print("xy error to green center (m):", xy_error)
print("expected red center z (m):", expected_red_z)
print("red stacked on green:", xy_error < 0.02 and final_red_pos[2] > final_green_pos[2])