# pepper_vlm

This package provides visual perception capabilities using the SmolVLM (Vision-Language Model). It describes the robot's surroundings in natural language.

## Nodes

### `pepper_vlm_node`
Instructs the SmolVLM model to describe images from the robot's camera.

- **Subscriptions**:
  - `/naoqi_driver/camera/front/image_raw` (`sensor_msgs/Image`): Raw camera feed from Pepper.
- **Publications**:
  - `/smolvlm/output` (`std_msgs/String`): Concise description of the scene, including people's characteristics (age, gender, emotion).

## Performance
- Uses `HuggingFaceTB/SmolVLM-500M-Instruct`.
- Optimized for edge devices (Jetson/Desktop) by resizing images to a longest edge of 512px.
- Throttled to `1 Hz` to maintain system stability.

## Requirements
- `torch`, `transformers`, `Pillow`, `cv_bridge`
- CUDA support is highly recommended for real-time performance.
