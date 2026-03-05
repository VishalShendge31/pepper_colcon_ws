# pepper_audio_transcriber

This package provides speech-to-text (STT) capabilities using OpenAI's Whisper model running locally. It can be configured to listen for a wake word.

## Nodes

### `whisper_transcriber`
Transcribes audio files into text strings.

- **Subscriptions**:
  - `pepper_audio` (`std_msgs/String`): Path to the audio file to transcribe.
- **Publications**:
  - `whisper_transcript` (`std_msgs/String`): The resulting transcribed text.

## Parameters
- `model` (string, default: `small`): The Whisper model size (tiny, base, small, medium, large).
- `lang` (string, default: `None`): Language code (e.g., `de`, `en`). If `None`, it auto-detects.
- `require_wake_word` (bool, default: `true`): Only publish transcript if a wake word (e.g., "Hey Pepper") is detected.

## Wake Word Support
The node includes a large list of wake word variations (e.g., "Hey Pepper", "Hallo Pepper", etc.) to account for transcription variations. When enabled, it waits for a wake word before buffering and publishing the subsequent question.
