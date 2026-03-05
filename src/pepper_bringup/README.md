# pepper_bringup

This package is the central entry point for launching the entire Pepper robot system. It contains the main launch file that orchestrates all functional nodes.

## Launching the System

### Prerequisites
Before running the launch file, ensure the following components are active:
1. **NaoQi Driver**: Running in a Docker container on the ROS 1 machine.
2. **ROS 1 Bridge**: Active on the ROS 2 machine.
3. **Pepper Server**: A Python script (`pepper_server.py`) running on the robot itself to handle motion and audio output.

### Usage
Run the unified launch file:
```bash
ros2 launch pepper_bringup pepper_bringup.launch.py openai_api_key:="your_key"
```

## Included Nodes
- `joy_node`: Controller input.
- `audio_receiver`: Capture audio from Pepper.
- `whisper_transcriber`: Speech-to-text.
- `openai_server`: LLM logic.
- `openai_bridge`: Context integration.
- `pepper_vlm`: Vision processing.
- `pepper_piper_tts`: Text-to-speech.
- `pepper_dashboard`: Web user interface.
