1. activate virtual environment:
. ~/rocker_venv/bin/activate

2. Inside this virtual environment run below command:
rocker --x11 --user --home --privileged \
  --volume /dev/shm /dev/shm \
  --network=host -- ros:noetic-ros-base-focal \
  'bash -c "sudo apt update && sudo apt install -y ros-noetic-rospy-tutorials tilix && tilix"'

3. above will open one tilix terminal. Inside that terminal paste below commands step by step
cd pepper_catkin_ws/
clone the drivers for pepper (NAOqi and all dependencies) # if not installed/cloned before
sudo apt update
sudo apt install ros-noetic-image-transport ros-noetic-tf2-geometry-msgs ros-noetic-diagnostic-updater ros-noetic-urdf ros-noetic-tf2-msgs
sudo apt install ros-noetic-cv-bridge ros-noetic-robot-state-publisher
sudo apt install libopencv-dev
sudo apt install libxmlrpcpp-dev
catkin_make -DCMAKE_CXX_FLAGS="-I/usr/include/opencv4" #only first time when you build pepper_catkin_ws

1. For launching the naoqi driver: in terminal one
cd pepper_catkin_ws
docker compose up -d
docker exec -it ros1_pepper_container bash
source /devel/setup.bash
roslaunch naoqi_driver naoqi_driver.launch nao_ip:=192.168.100.163 qi_listen_url:=tcp://0.0.0.0:56000 network_interface:=docker0 10.219.165.53

roslaunch naoqi_driver naoqi_driver.launch nao_ip:=10.171.8.53 qi_listen_url:=tcp://0.0.0.0:56000 network_interface:=docker0 10.219.165.53

2. Start the ROS bridge
Terminal-2: Start the ROS1 bridge node from the ROS2 Humble system.
In a new terminal window, 
source /opt/ros/humble/setup.bash
source ~/ros-humble-ros1-bridge/install/local_setup.bash
ros2 run ros1_bridge dynamic_bridge

3. ssh inside pepper using 3rd terminal
#ssh nao@192.168.100.20
ssh nao@192.168.100.163
python pepper_server.py

4. Now start the ros2 nodes in different terminals
source /opt/ros/humble/setup.bash
source ~/pepper_venv/bin/activate
source ws/install/setup.bash

ros2 run joy joy_node

ros2 run pepper_audio_receiver audio_receiver

ros2 run pepper_audio_transcriber whisper_transcriber

ros2 launch openai_server openai_server_launch.py   openai_api_key:=[REDACTED_API_KEY]   openai_model:=gpt-5-nano

ros2 run openai_bridge transcription_to_openai 

ros2 run pepper_vlm pepper_vlm_node

ros2 run pepper_piper_tts pepper_piper_node

ros2 run pepper_dashboard pepper_dashboard_server


ros2 run pepper_orpheus_tts pepper_orpheus_tts_node

ros2 run pepper_audio_transcriber whisper_transcriber --ros-args -p require_wake_word:=false -p lang:=de

1. Install OpenAI Whisper using:

pip install -U openai-whisper

#!/home/robot/pepper_venv/bin/python3



