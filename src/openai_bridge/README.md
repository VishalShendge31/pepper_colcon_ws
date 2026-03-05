# openai_bridge

This package bridges audio transcriptions and visual context to the OpenAI server for processing. It combines data from the Whisper transcriber and the SmolVLM vision model to provide context-aware prompts to the LLM.

## Nodes

### `transcription_to_openai`
Listens for user speech and visual descriptions, then sends a combined query to the OpenAI server.

- **Subscriptions**:
  - `whisper_transcript` (`std_msgs/String`): The text result of the user's speech.
  - `/smolvlm/output` (`std_msgs/String`): The latest visual description from the camera.
- **Publications**:
  - `openai_response` (`std_msgs/String`): The text response received from the OpenAI server.
- **Service Clients**:
  - `/openai_ask` (`openai_server_interfaces/srv/OpenaiServer`): Service to get responses from OpenAI.

## Parameters
- `reset_conversation` (bool, default: `true`): Whether to clear chat history for each new request.
- `pre_prompt` (string): System instruction for the AI (e.g., "Respond concisely in German").
