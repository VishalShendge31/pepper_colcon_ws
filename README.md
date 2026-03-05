# Pepper AI ROS 2 Workspace (pepper_colcon_ws)

This repository contains a comprehensive ROS 2 workspace designed to integrate the **Pepper Robot** with advanced AI capabilities, including Large Language Models (LLMs), Vision-Language Models (VLMs), and modern Text-to-Speech (TTS) engines.

## 🚀 Overview

The workspace acts as a high-performance bridge between the legacy Naoqi environment (running on Pepper) and a modern ROS 2 Humble environment (running on a Jetson or PC). It enables Pepper to perceive its environment through vision and audio, process that data using state-of-the-art AI, and interact naturally with humans.

## 🏗 Architecture

The system follows a distributed architecture:
1.  **Naoqi Side**: `pepper_server.py` runs on the robot, handling low-level hardware access (audio recording, tablet display, motion, battery polling).
2.  **ROS 2 Side**: Multiple packages handle audio processing, AI inference (Whisper, OpenAI, Piper TTS), and the user interface.
3.  **Communication**: High-speed TCP sockets are used for audio streaming between the robot and the ROS 2 host.

## 🌟 Key Features

-   **Intelligent Perception**: Whisper-based ASR for high-accuracy speech-to-text.
-   **Vision-Language Capabilities**: VLM integration for environmental description.
-   **Natural Interaction**: Text-to-Speech via Piper and Orpheus, integrated with OpenAI for reasoning.
-   **Monitoring & Control**: Web-based dashboard for real-time robot status and AI responses.
-   **Hardware Interfaces**: Support for PS4 controllers and keyboard teleop.

## 📦 Package Breakdown

| Package | Description |
| :--- | :--- |
| **`pepper_bringup`** | Central launch package to start all necessary nodes. |
| **`pepper_audio_receiver`** | Receives raw audio chunks from the robot via TCP. |
| **`pepper_audio_transcriber`** | Transcribes audio using OpenAI Whisper. |
| **`openai_bridge`** | Connects transcriptions to OpenAI GPT for reasoning and response generation. |
| **`pepper_vlm`** | Provides Vision-Language Model capabilities for image description. |
| **`pepper_piper_tts`** | High-quality local Text-to-Speech using Piper. |
| **`pepper_dashboard`** | Web-based interface for monitoring robot state and AI logs. |
| **`pepper_teleop`** | Keyboard-based control for Pepper's movement. |
| **`pepper_Ps4`** | Joystick control using a PS4 controller. |
| **`openai-api-ros2-service`** | Core service interfaces for OpenAI communication. |

## 🛠 Prerequisites

-   **OS**: Ubuntu 22.04 LTS (Jammy Jellyfish)
-   **ROS 2**: Humble Hawksbill
-   **Python Dependencies**: (See [requirements.txt](requirements.txt))
    -   `naoqi` (for the robot-side script)
    -   `openai-whisper`
    -   `openai`
    -   `Flask` (for the dashboard)
    -   `piper-tts`

## 🚀 Getting Started

### 1. Build the Workspace
```bash
cd ~/pepper_colcon_ws
colcon build --symlink-install
source install/setup.bash
```

### 2. Start the Robot Bridge
On the Pepper robot (Naoqi environment):
```bash
python pepper_server.py
```

### 3. Launch the ROS 2 Stack
```bash
ros2 launch pepper_bringup pepper_complete_launch.py
```

## 📊 Dashboard
Once the system is running, the dashboard is accessible at:
`http://<HOST_PC_IP>:5000/`

It displays:
-   Real-time Camera Feed
-   Audio Transcription Logs
-   AI Reasoning & Responses
-   Battery Status & System Time

---
**Maintainer**: [Vishal Shendge](mailto:shendge.vishal.vilas@gmail.com)
