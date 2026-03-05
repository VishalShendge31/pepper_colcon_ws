# openai_server

This ROS 2 package provides a server node that interacts with OpenAI's Chat Completion API (e.g., GPT-4o). It maintains conversation history and can be used to provide intelligent responses for the Pepper robot.

## Features
- Provides the `/openai_ask` ROS 2 service.
- Supports persistent conversation history and session resetting.
- Allows specifying a `pre_prompt` (system message) for each request.
- Configurable OpenAI model (default: `gpt-4o`).

## Dependencies
- `rclcpp`
- `std_msgs`
- `openai_server_interfaces`
- `CURL`
- `nlohmann_json`

## Parameters
- `openai_api_key` (string, required): Your OpenAI API key.
- `openai_model` (string, default: `gpt-4o`): The model to use for completion.

## Usage
Run the node with your API key:
```bash
ros2 run openai_server openai_server_node --ros-args -p openai_api_key:="your_key_here"
```

### Service Interface: `openai_server_interfaces/srv/OpenaiServer`
- **Request**:
  - `string prompt`: The user's input text.
  - `bool reset_conversation`: If true, clears the history before this request.
  - `string pre_prompt`: An optional system instruction to guide the AI's behavior.
- **Response**:
  - `string response`: The AI-generated text.
