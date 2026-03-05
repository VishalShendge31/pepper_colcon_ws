# pepper_Ps4

This package allows teleoperating the Pepper robot using a DualShock 4 (PS4) controller. It maps joystick axes and buttons to velocity commands.

## Nodes

### `teleop_ps4`
Translates joystick inputs from the `/joy` topic into `geometry_msgs/Twist` commands.

- **Subscriptions**:
  - `/joy` (`sensor_msgs/Joy`): Raw joystick input.
- **Publications**:
  - `cmd_vel` (`geometry_msgs/Twist`): Velocity commands for the robot.

## Parameters
- `cmd_vel_topic` (string, default: `cmd_vel`): The topic to publish velocity commands to.
- `axis_linear` (int, default: `1`): Index of the axis for forward/backward movement.
- `axis_angular` (int, default: `0`): Index of the axis for rotation.
- `scale_linear` (float, default: `0.25`): Scaling factor for linear speed.
- `scale_angular` (float, default: `0.8`): Scaling factor for angular speed.
- `enable_button` (int, default: `5`): Index of the "deadman" button (must be held to move).
- `turbo_button` (int, default: `1`): Index of the button for increased speed.
- `deadzone` (float, default: `0.05`): Ignore small movements of the sticks.
