#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
import socket
import struct
import threading
import os
import time
import glob
import numpy as np
import scipy.io.wavfile as wavfile
import noisereduce as nr

HOST = "0.0.0.0" 
PORT = 5005       

def recv_all(sock, size):
    data = b""
    while len(data) < size:
        packet = sock.recv(min(4096, size - len(data)))
        if not packet:
            return None
        data += packet
    return data

class PepperAudioReceiver(Node):
    def __init__(self):
        super().__init__('pepper_audio_receiver')

        self.declare_parameter('audio_save_dir', '/home/robot/pepper_colcon_ws/audio_chunks')
        self.audio_save_dir = self.get_parameter('audio_save_dir').get_parameter_value().string_value
        
        if not os.path.exists(self.audio_save_dir):
            os.makedirs(self.audio_save_dir, exist_ok=True)
            self.get_logger().info(f"Created directory: {self.audio_save_dir}")

        self.cleanup_old_audio()  # Clean up at startup
        self.get_logger().info("Startup cleanup complete.")

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.VOLATILE
        )
        self.publisher_ = self.create_publisher(String, 'pepper_audio', qos)

        self.get_logger().info(f"Audio chunks will be saved to: {self.audio_save_dir}")
        self.get_logger().info(f"Starting TCP server on {HOST}:{PORT}")
        
        self.server_thread = threading.Thread(target=self.tcp_server)
        self.server_thread.daemon = True
        self.server_thread.start()

        self.cleanup_timer = self.create_timer(60.0, self.cleanup_old_audio_timer)

    def cleanup_old_audio(self):
        files = glob.glob(os.path.join(self.audio_save_dir, "*.wav"))
        for f in files:
            try:
                os.remove(f)
            except Exception as e:
                self.get_logger().error(f"Failed to delete {f}: {e}")

    def cleanup_old_audio_timer(self):
        current_time = time.time()
        files = glob.glob(os.path.join(self.audio_save_dir, "*.wav"))
        count = 0
        for f in files:
            try:
                # 180 seconds = 3 minutes
                if current_time - os.path.getmtime(f) > 180:
                    os.remove(f)
                    count += 1
            except Exception as e:
                pass
        if count > 0:
            self.get_logger().info(f"Cleaned up {count} audio chunks older than 3 minutes.")

    def tcp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(1)
            while rclpy.ok():
                self.get_logger().info("Waiting for Pepper connection...")
                try:
                    conn, addr = s.accept()
                    with conn:
                        self.get_logger().info(f"Connected by {addr}")
                        while rclpy.ok():
                            size_bytes = recv_all(conn, 8)
                            if not size_bytes:
                                self.get_logger().info("Connection closed by client")
                                break
                            audio_size = struct.unpack(">Q", size_bytes)[0]

                            audio_data = recv_all(conn, audio_size)
                            if not audio_data:
                                self.get_logger().info("Connection closed while receiving audio")
                                break

                            timestamp = int(time.time() * 1000)
                            audio_path = os.path.join(self.audio_save_dir, f"chunk_{timestamp}.wav")
                            
                            try:
                                # Convert raw bytes to 16-bit PCM numpy array
                                # Pepper records 1 channel, 16000Hz, 16-bit
                                audio_np = np.frombuffer(audio_data, dtype=np.int16)
                                
                                # Apply Noise Reduction (stationary noise reduction)
                                reduced_noise = nr.reduce_noise(y=audio_np, sr=16000, stationary=True, prop_decrease=0.8)
                                
                                # Save the cleaned audio to wav file
                                wavfile.write(audio_path, 16000, reduced_noise)
                                
                            except Exception as e:
                                self.get_logger().error(f"Failed to process and save audio: {e}")
                                continue

                            msg = String()
                            msg.data = audio_path
                            self.publisher_.publish(msg)
                            self.get_logger().info(f"Published chunk {audio_path}")
                except Exception as e:
                    self.get_logger().error(f"TCP socket error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = PepperAudioReceiver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down Pepper Audio Receiver")
    finally:
        node.cleanup_old_audio()  # Clean up at shutdown
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
