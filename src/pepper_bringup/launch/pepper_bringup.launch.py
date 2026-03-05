"""
pepper_bringup.launch.py
------------------------
Launches all ROS2 nodes needed for the Pepper robot system.

PREREQUISITES (run manually before launching this file):
  1. NaoQi driver (Docker container on the ROS1 machine):
       cd pepper_catkin_ws && docker compose up -d
       docker exec -it ros1_pepper_container bash
       source pepper_catkin_ws/devel/setup.bash
       roslaunch naoqi_driver naoqi_driver.launch \\
           nao_ip:=192.168.100.163 \\
           qi_listen_url:=tcp://0.0.0.0:56000 \\
           network_interface:=docker0

  2. ROS1 bridge (on this machine):
       source /opt/ros/humble/setup.bash
       source ~/ros-humble-ros1-bridge/install/local_setup.bash
       ros2 run ros1_bridge dynamic_bridge

  3. Pepper server (SSH into robot):
       ssh nao@192.168.100.163
       python pepper_server.py

USAGE:
  source /opt/ros/humble/setup.bash
  source ~/pepper_venv/bin/activate
  source ~/ws/install/setup.bash
  ros2 launch pepper_bringup pepper_bringup.launch.py \\
      openai_api_key:=<YOUR_KEY> openai_model:=gpt-4o
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # ── Launch Arguments ────────────────────────────────────────────────────
    openai_api_key_arg = DeclareLaunchArgument(
        'openai_api_key',
        default_value='ENTER_YOUR_OPENAI_API_KEY_HERE',
        description='OpenAI API key (do not commit to version control!)'
    )

    openai_model_arg = DeclareLaunchArgument(
        'openai_model',
        default_value='gpt-4o',
        description='OpenAI model to use (e.g. gpt-4o, gpt-3.5-turbo)'
    )

    # ── Nodes ────────────────────────────────────────────────────────────────

    # 1. Joystick / PS4 controller input
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
    )

    # 2. Audio capture from Pepper microphones
    audio_receiver_node = Node(
        package='pepper_audio_receiver',
        executable='audio_receiver',
        name='pepper_audio_receiver',
        output='screen',
    )

    # 3. Whisper-based speech-to-text transcriber
    whisper_transcriber_node = Node(
        package='pepper_audio_transcriber',
        executable='whisper_transcriber',
        name='whisper_transcriber',
        output='screen',
    )

    # 4. OpenAI server (LLM reasoning backend)
    openai_server_node = Node(
        package='openai_server',
        executable='openai_server_node',
        name='openai_server',
        output='screen',
        parameters=[{
            'openai_api_key': LaunchConfiguration('openai_api_key'),
            'openai_model':   LaunchConfiguration('openai_model'),
        }],
    )

    # 5. Bridge that forwards transcription results to OpenAI
    transcription_to_openai_node = Node(
        package='openai_bridge',
        executable='transcription_to_openai',
        name='transcription_to_openai',
        output='screen',
    )

    # 6. Vision-Language Model node (camera perception)
    pepper_vlm_node = Node(
        package='pepper_vlm',
        executable='pepper_vlm_node',
        name='pepper_vlm',
        output='screen',
    )

    # 7. Piper TTS — converts text responses to Pepper speech
    pepper_piper_tts_node = Node(
        package='pepper_piper_tts',
        executable='pepper_piper_node',
        name='pepper_piper_tts',
        output='screen',
    )

    # 8. Web dashboard server
    pepper_dashboard_node = Node(
        package='pepper_dashboard',
        executable='pepper_dashboard_server',
        name='pepper_dashboard',
        output='screen',
    )

    return LaunchDescription([
        # Arguments
        openai_api_key_arg,
        openai_model_arg,

        # Nodes (started in dependency order)
        joy_node,
        audio_receiver_node,
        whisper_transcriber_node,
        openai_server_node,
        transcription_to_openai_node,
        pepper_vlm_node,
        pepper_piper_tts_node,
        pepper_dashboard_node,
    ])
