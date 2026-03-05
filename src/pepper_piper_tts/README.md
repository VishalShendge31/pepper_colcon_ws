# pepper_piper_tts

This package provides fast, local text-to-speech using the Piper TTS engine. It is optimized for low-latency voice output on edge devices.

## Nodes

### `piper_tts`
Converts text to speech using ONNX models and streams audio to Pepper.

- **Subscriptions**:
  - `openai_response` (`std_msgs/String`): Input text for synthesis.

## Parameters
- `voice_model` (string): Path to the `.onnx` voice model file.
- `pepper_ip`: IP address of the Pepper robot.
- `tts_port` (default: `5005`): TCP port for audio streaming.
- `piper_binary`: Path to the `piper` executable.

## Features
- Efficient ONNX-based synthesis.
- Automatic reconnection to the robot's audio server.
- Built-in self-test for engine verification.
