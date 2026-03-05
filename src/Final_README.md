# How to Run: Pepper AI ROS 2 System

Please refer to the root [How_To_Run.md](../How_To_Run.md) for the most up-to-date and detailed execution instructions.

## Quick Summary
1. **Launch ROS 1 Driver** (inside Docker).
2. **Start ROS 1 Bridge**.
3. **Run Pepper Server** (via SSH on robot).
4. **Launch ROS 2 AI Stack**:
   ```bash
   ros2 launch pepper_bringup pepper_bringup.launch.py openai_api_key:=<KEY>
   ```
