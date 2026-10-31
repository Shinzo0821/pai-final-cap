# Code block 0
import numpy as np

# Open gripper before grasping
open_gripper()

# Get object poses and extents for the red cube and green cube
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

# Sample grasp pose for the red cube
grasp_pos, grasp_quat = sample_grasp_pose("red cube")

# Calculate gripper Z offset relative to the center of the red cube when grasped
grasp_z_offset = grasp_pos[2] - red_pos[2]

# Approach and go to grasp pose for the red cube
goto_pose(grasp_pos, grasp_quat, z_approach=0.1)

# Close gripper to grasp the red cube
close_gripper()

# Lift the red cube straight up to avoid collisions during transit
lift_pos = grasp_pos.copy()
lift_pos[2] += 0.15
goto_pose(lift_pos, grasp_quat)

# Calculate the exact Z height for the red cube's center when resting on top of the green cube:
# Top of green cube is green_pos[2] + green_extent[2] / 2.0
# Center of red cube should be red_extent[2] / 2.0 above the top of the green cube
target_red_center_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)

# Account for the grasp Z offset between the gripper and the red cube center
place_pos = np.array([
    green_pos[0],
    green_pos[1],
    target_red_center_z + grasp_z_offset
])

# Move above the green cube and gently lower the red cube onto it
goto_pose(place_pos, grasp_quat, z_approach=0.1)

# Open the gripper to release the red cube gently
open_gripper()

# Retract the gripper upward after releasing
retract_pos = place_pos.copy()
retract_pos[2] += 0.1
goto_pose(retract_pos, grasp_quat)

# Code block 1
import numpy as np

# Check current poses of the red and green cubes to verify task completion
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

expected_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)
xy_dist = np.linalg.norm(red_pos[:2] - green_pos[:2])
z_diff = abs(red_pos[2] - expected_z)

print(f"Red pos: {red_pos}, Green pos: {green_pos}, Expected Z: {expected_z}")
print(f"XY dist: {xy_dist:.4f}, Z diff: {z_diff:.4f}")

# If the red cube is not properly stacked on the green cube, retry placement
if xy_dist > 0.03 or z_diff > 0.02:
    print("Task not complete, retrying...")
    open_gripper()
    grasp_pos, grasp_quat = sample_grasp_pose("red cube")
    grasp_z_offset = grasp_pos[2] - red_pos[2]
    
    goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
    close_gripper()
    
    lift_pos = grasp_pos.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)
    
    place_pos = np.array([
        green_pos[0],
        green_pos[1],
        expected_z + grasp_z_offset
    ])
    
    goto_pose(place_pos, grasp_quat, z_approach=0.1)
    open_gripper()
    
    retract_pos = place_pos.copy()
    retract_pos[2] += 0.1
    goto_pose(retract_pos, grasp_quat)
else:
    print("Task successfully completed!")

# Code block 2
import numpy as np

# Check current poses of the red and green cubes to verify if the retry succeeded
red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)

expected_z = green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)
xy_dist = np.linalg.norm(red_pos[:2] - green_pos[:2])
z_diff = abs(red_pos[2] - expected_z)

print(f"After retry - Red pos: {red_pos}, Green pos: {green_pos}, Expected Z: {expected_z}")
print(f"After retry - XY dist: {xy_dist:.4f}, Z diff: {z_diff:.4f}")

if xy_dist > 0.025 or z_diff > 0.02:
    print("Still not stacked, executing careful pick and place...")
    open_gripper()
    
    # Re-fetch poses
    red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
    green_pos, _, green_extent = get_object_pose("green cube", return_bbox_extent=True)
    
    grasp_pos, grasp_quat = sample_grasp_pose("red cube")
    print(f"Sampled grasp_pos: {grasp_pos}, grasp_quat: {grasp_quat}")
    
    # Compute full 3D offset between grasp pose and object center
    grasp_offset = grasp_pos - red_pos
    
    # Approach from above and grasp
    goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
    close_gripper()
    
    # Check if grasped by lifting
    lift_pos = grasp_pos.copy()
    lift_pos[2] += 0.15
    goto_pose(lift_pos, grasp_quat)
    
    red_pos_lifted, _, _ = get_object_pose("red cube", return_bbox_extent=False)
    print(f"Red pos after lift: {red_pos_lifted}")
    
    # If lift failed to raise the cube, try top-down grasp directly at red_pos
    if red_pos_lifted[2] < red_pos[2] + 0.05:
        print("Grasp with sampled pose slipped/missed, trying direct top-down grasp...")
        open_gripper()
        red_pos, _, red_extent = get_object_pose("red cube", return_bbox_extent=True)
        top_down_quat = np.array([0.0, 0.0, 1.0, 0.0])
        grasp_pos = red_pos.copy()
        grasp_quat = top_down_quat
        grasp_offset = np.zeros(3)
        
        goto_pose(grasp_pos, grasp_quat, z_approach=0.1)
        close_gripper()
        
        lift_pos = grasp_pos.copy()
        lift_pos[2] += 0.15
        goto_pose(lift_pos, grasp_quat)
    
    # Compute target placement position accounting for grasp offset
    target_red_center = np.array([
        green_pos[0],
        green_pos[1],
        green_pos[2] + (green_extent[2] / 2.0) + (red_extent[2] / 2.0)
    ])
    place_pos = target_red_center + grasp_offset
    
    # Move above and gently place the red cube on the green cube
    goto_pose(place_pos, grasp_quat, z_approach=0.1)
    
    # Open the gripper
    open_gripper()
    
    # Verify final state
    red_final, _, _ = get_object_pose("red cube", return_bbox_extent=False)
    green_final, _, _ = get_object_pose("green cube", return_bbox_extent=False)
    print(f"Final Red pos: {red_final}, Final Green pos: {green_final}")