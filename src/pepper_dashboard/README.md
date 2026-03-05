# pepper_dashboard

This package provides a web-based dashboard for monitoring and interacting with the Pepper robot in real-time.

## Features
- **Live Camera Feed**: Real-time visualization of what the robot sees.
- **AI Status Monitoring**: Displays current ASR transcripts, VLM descriptions, and LLM responses.
- **Robot State**: Shows battery level and connection status.
- **Log Visualization**: Tracks the reasoning process of the robot.

## Nodes

### `pepper_dashboard_server`
A Flask-based web server that integrates with ROS 2.

- **URL**: `http://localhost:5000`
- **Subscriptions**:
  - `/naoqi_driver/camera/front/image_raw` (`sensor_msgs/Image`)
  - `pepper_audio` (`std_msgs/String`)
  - `whisper_transcript` (`std_msgs/String`)
  - `openai_response` (`std_msgs/String`)
  - `/smolvlm/output` (`std_msgs/String`)

## Static Assets
The dashboard uses custom logos and styles stored in the `static` directory within the module.
