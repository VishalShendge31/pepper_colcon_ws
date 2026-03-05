# pepper_audio_receiver

This package captures raw audio data from the Pepper robot over a TCP connection, processes it, and publishes the location of the resulting audio files.

## Nodes

### `audio_receiver`
Runs a TCP server that waits for connections from the Pepper robot. It receives 16kHz, 16-bit PCM audio, applies noise reduction, and saves it as temporary `.wav` files.

- **TCP Server**: Listens on port `5005`.
- **Publications**:
  - `pepper_audio` (`std_msgs/String`): Path to the latest processed audio `.wav` file.

## Parameters
- `audio_save_dir` (string, default: `/home/robot/pepper_colcon_ws/audio_chunks`): Directory where temporary audio files are stored.

## Features
- Automatic cleanup of audio files older than 3 minutes.
- Real-time stationary noise reduction using `noisereduce`.
