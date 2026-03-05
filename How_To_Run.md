# How to Run: Pepper AI ROS 2 System

This guide provides a structured workflow to bring up the full Pepper AI integration using ROS 1, ROS 2, and the Naoqi bridge.

## 📋 System Requirements
- **Hardware**: Pepper Robot, Host PC/Jetson (Ubuntu 22.04).
- **Network**: Both devices must be on the same local network.
- **Docker**: Installed on the Host PC for ROS 1 compatibility and ROS 2 environment.

---

## 🚀 Execution Flow

Follow these steps in separate terminals (or using `tmux`).

### 1. Terminal 1: ROS 1 Naoqi Driver (Docker)
Starts the bridge that connects to Pepper's hardware.
```bash
cd ~/pepper_catkin_ws
docker compose up -d
docker exec -it ros1_pepper_container bash
source /devel/setup.bash
roslaunch naoqi_driver naoqi_driver.launch \
    nao_ip:=192.168.100.163 \
    qi_listen_url:=tcp://0.0.0.0:56000 \
    network_interface:=docker0
```

### 2. Terminal 2: ROS 1 <-> ROS 2 Bridge (Docker)
Enables communication between the ROS 1 driver and the ROS 2 AI stack.
```bash
docker run --rm -it \
    --network=host \
    -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    -v $HOME:/home/user \
    dustynv/ros:humble-desktop-l4t-r36.4.0 \
    bash -c "source /home/user/ros-humble-ros1-bridge/install/local_setup.bash && \
             export ROS_MASTER_URI=http://10.81.162.71:11311 && \
             ros2 run ros1_bridge dynamic_bridge --bridge-all-topics"
```

### 3. Terminal 3: Pepper Robot Server (SSH)
Connect to the robot to run the low-level audio and tablet bridge.
```bash
ssh nao@<PEPPER_IP>
python pepper_server.py
```

### 4. Terminal 4: ROS 2 AI Container
Start the ROS 2 environment where your workspace is located.
```bash
docker run -it --rm \
    --network=host \
    --env DISPLAY=$DISPLAY \
    -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $HOME:/home/user \
    dustynv/ros:humble-desktop-l4t-r36.4.0
```

**Inside the ROS 2 Container:**
```bash
source pepper_colcon_ws/install/setup.bash
ros2 launch pepper_bringup pepper_bringup.launch.py \
    openai_api_key:=<YOUR_OPENAI_KEY> \
    openai_model:=gpt-4o
```

---

## 🛠 Manual Node Execution (Optional)
If you need to debug specific components, you can run nodes individually inside the ROS 2 container after completing steps 1-3.

| Component | Command |
| :--- | :--- |
| **Audio Receiver** | `ros2 run pepper_audio_receiver audio_receiver` |
| **Transcriber** | `ros2 run pepper_audio_transcriber whisper_transcriber` |
| **OpenAI Bridge** | `ros2 run openai_bridge transcription_to_openai` |
| **VLM Node** | `ros2 run pepper_vlm pepper_vlm_node` |
| **Piper TTS** | `ros2 run pepper_piper_tts pepper_piper_node` |
| **Dashboard** | `ros2 run pepper_dashboard pepper_dashboard_server` |

---

## 📊 Monitoring
Open your browser and navigate to:
`http://localhost:5000/`

This dashboard provides real-time visualization of the AI's reasoning, transcriptions, and the robot's camera feed.
