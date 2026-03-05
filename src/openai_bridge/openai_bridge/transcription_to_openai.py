#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from openai_server_interfaces.srv import OpenaiServer

class TranscriptionToOpenaiNode(Node):
    def __init__(self):
        super().__init__('transcription_to_openai')
        
        # Declare parameters for configurability
        self.declare_parameter('reset_conversation', True)
        self.declare_parameter('pre_prompt', (
    'You are a helpful robot assistant. Respond concisely in German in one short sentence. '
    'You will be provided with a [Visual Context] block containing a description of what you are currently seeing through your camera. '
    'Use this visual context to help answer the user\'s question creatively, but do not explicitly mention that you "see a description". Talk as if you are looking at it with your own eyes.'
))   
        #self.declare_parameter('pre_prompt', 'You are a helpful robot assistant. Respond concisely in German in very short one sentence. Identify emotion from the question and in the response add this special tokens as per the emotion. for happy <laughing>, <chuckles>, <giggles>. for sad <sighs>, <sniffs>, <inhales deeply>. for neutral <hm>, <breath>, <pause>. for angry <growls>, <breathes heavily>, <snarles>, <exclaims>. for worried <shaky_breath>, <sigh>, <tremble>, <nervous_laugh>. for disgusted <ugh>, <scoff>, <tsk>, <ew>, <breath>. for whisper <soft>, <hush>, <quiet>. for sleppy <tired>, <mumble>, <softsigh>, <yawn>, <slowbreath>. This are some examples for each emotion: 1. for angry: <angry><growl> Endlich Wochenende, ich brauch echt mal Pause!<grit> for disgusted: <disgusted><ugh> Endlich Wochenende, ich brauch echt mal Pause! <hm> for happy: <laughing> Endlich Wochenende, ich brauch echt mal Pause! <chuckles> for neutral <Neutral><breath> Endlich Wochenende, ich brauch echt mal Pause! <pause> for sad:  <sighs> Endlich Wochenende, ich brauch echt mal Pause! <thoughtful>. for sleepy: <sleepy><yawn> Endlich Wochenende, ich brauch echt mal Pause! <sigh-light> for whisper: <whisper><quiet>Endlich Wochenende, ich brauch echt mal Pause! <hm> for worried: <worried><breath> Endlich Wochenende, ich brauch echt mal Pause! <um>')
        
        self.reset_conversation = self.get_parameter('reset_conversation').get_parameter_value().bool_value
        self.pre_prompt = self.get_parameter('pre_prompt').get_parameter_value().string_value
        
        self.get_logger().info(f'Reset conversation: {self.reset_conversation}')
        self.get_logger().info(f'Pre-prompt: {self.pre_prompt}')
        
        # Cache for latest VLM description
        self.latest_vlm_description = ""
        
        # Subscribe to VLM output
        self.vlm_subscription = self.create_subscription(
            String,
            '/smolvlm/output',
            self.vlm_callback,
            10)
        self.get_logger().info('Listening to /smolvlm/output topic...')
        
        # Subscribe to Whisper output
        self.subscription = self.create_subscription(
            String,
            'whisper_transcript',
            self.transcript_callback,
            10)
        self.get_logger().info('Listening to whisper_transcript topic...')
        
        # Publish to TTS
        self.openai_publisher = self.create_publisher(
            String,
            'openai_response',  
            10)
        self.get_logger().info('Publishing OpenAI responses to openai_response topic...')

        # Create OpenAI service client
        self.cli = self.create_client(OpenaiServer, '/openai_ask')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /openai_ask service...')
        self.get_logger().info('Connected to /openai_ask service.')

    def vlm_callback(self, msg):
        # Update the latest VLM description as it streams in
        if msg.data and msg.data.strip():
            self.latest_vlm_description = msg.data.strip()
            self.get_logger().debug(f'Cached new VLM description: "{self.latest_vlm_description}"')

    def transcript_callback(self, msg):
        self.get_logger().info(f'Received transcript: "{msg.data}"')
        
        # Skip empty transcripts
        if not msg.data.strip():
            self.get_logger().warn('Empty transcript received, skipping...')
            return
        
        # Combine VLM context and user question
        if self.latest_vlm_description:
            combined_prompt = f"[Visual Context from Robot Camera: {self.latest_vlm_description}]\nUser Question: {msg.data}"
        else:
            combined_prompt = msg.data

        self.get_logger().info(f'Sending to OpenAI: "{combined_prompt}"')

        # Prepare service request
        request = OpenaiServer.Request()
        request.prompt = combined_prompt
        request.reset_conversation = self.reset_conversation
        request.pre_prompt = self.pre_prompt
        
        # Call OpenAI service
        future = self.cli.call_async(request)
        future.add_done_callback(self.service_response_callback)

    def service_response_callback(self, future):
        try:
            response = future.result()
            self.get_logger().info(f'OpenAI response: "{response.response}"')

            # Publish the response to TTS
            response_msg = String()
            response_msg.data = response.response
            self.openai_publisher.publish(response_msg)
            self.get_logger().info(f'Published response to openai_response topic for TTS')

        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = TranscriptionToOpenaiNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
