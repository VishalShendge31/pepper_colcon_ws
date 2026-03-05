1. For launching the naoqi driver start the ros1 container
cd pepper_catkin_ws
docker compose up -d
docker exec -it ros1_pepper_container bash
source /devel/setup.bash
roslaunch naoqi_driver naoqi_driver.launch nao_ip:=192.168.100.163 qi_listen_url:=tcp://0.0.0.0:56000 network_interface:=docker0 10.219.165.53

roslaunch naoqi_driver naoqi_driver.launch nao_ip:=10.171.8.53 qi_listen_url:=tcp://0.0.0.0:56000 network_interface:=docker0 10.219.165.53

2. Start the ROS bridge
Terminal-2: Start the ROS1 bridge node from the ROS2 Humble system.
docker run --rm -it \
		  --network=host \
		  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
		  -v $HOME:/home/user \
		  dustynv/ros:humble-desktop-l4t-r36.4.0 \
		  bash -c "source /home/user/ros-humble-ros1-bridge/install/local_setup.bash && \
			   export ROS_MASTER_URI=http://10.81.162.71:11311 && \
			   ros2 run ros1_bridge dynamic_bridge --bridge-all-topics"

3. ssh inside pepper using 3rd terminal
#ssh nao@192.168.100.20
ssh nao@192.168.100.163
python pepper_server.py

4. Now start the ros2 nodes in different terminals
start thr ros2 docker:
docker run -it --rm \
		  --network=host \
		  --env DISPLAY=$DISPLAY \
		  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
		  -v /tmp/.X11-unix:/tmp/.X11-unix \
		  -v $HOME:/home/user \
		  dustynv/ros:humble-desktop-l4t-r36.4.0

source pepper_colcon_ws/install/setup.bash

ros2 run joy joy_node

ros2 run pepper_audio_receiver audio_receiver

ros2 run pepper_audio_transcriber whisper_transcriber

ros2 launch openai_server openai_server_launch.py   openai_api_key:=<key> openai_model:=gpt-5-nano

ros2 run openai_bridge transcription_to_openai 

ros2 run pepper_vlm pepper_vlm_node

ros2 run pepper_piper_tts pepper_piper_node

ros2 run pepper_dashboard pepper_dashboard_server


ros2 run pepper_orpheus_tts pepper_orpheus_tts_node

ros2 run pepper_audio_transcriber whisper_transcriber --ros-args -p require_wake_word:=false -p lang:=de





