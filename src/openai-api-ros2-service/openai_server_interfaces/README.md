# openai_server_interfaces

This package defines the custom ROS 2 service interfaces used by the `openai_server` and `openai_bridge` packages.

## Interfaces

### Service: `OpenaiServer`
Used to send prompts to the OpenAI server and receive a text response.

**Definition (`srv/OpenaiServer.srv`):**
```text
string prompt
bool reset_conversation
string pre_prompt
---
string response
```

## Dependencies
- `std_msgs`
- `rosidl_default_generators`
