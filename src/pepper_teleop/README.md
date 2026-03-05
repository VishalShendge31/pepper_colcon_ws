# pepper_teleop

This package provides keyboard-based teleoperation for the Pepper robot, allowing users to control its movement using simple keystrokes.

## Nodes

### `teleop_keyboard`
Captures keyboard input and publishes velocity commands.

- **Publications**:
  - `cmd_vel` (`geometry_msgs/Twist`): Movement commands.

## Key Bindings

### Movement
- `w`: Forward
- `s`: Backward
- `a`: Turn Left
- `d`: Turn Right
- `u` / `o`: Diagonal Forward Left / Right
- `m` / `.`: Diagonal Backward Left / Right
- `k`: Stop

### Speed Control
- `q` / `y`: Increase / decrease linear velocity by 10%
- `w` / `x`: Increase / decrease angular velocity by 10%

## Usage
Run the keyboard teleop node:
```bash
ros2 run pepper_teleop teleop_keyboard
```
*Note: The terminal window must be active to capture keystrokes.*