#!/usr/bin/env python3
import os
import time
import torch
import whisper
import numpy as np

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class WhisperTranscriberNode(Node):
    def __init__(self):
        super().__init__('whisper_transcriber')

        # Parameters
        self.declare_parameter('lang', 'None')
        self.declare_parameter('model', 'small')
        self.declare_parameter('require_wake_word', True)
        
        model_size = self.get_parameter('model').get_parameter_value().string_value
        self.require_wake_word = self.get_parameter('require_wake_word').get_parameter_value().bool_value

        self.model = self.load_whisper(model_size)

        self.pub_transcript = self.create_publisher(String, 'whisper_transcript', 10)
        self.sub_audio = self.create_subscription(String, 'pepper_audio', self.audio_callback, 10)

        # State machine
        self.state = "IDLE" if self.require_wake_word else "DIRECT"
        self.question_buffer = ""
        self.last_audio_time = 0
        self.silence_timeout = 2.5

        # MASSIVELY EXTENDED wake word list (covers all Whisper mis-transcriptions)
        self.wake_words = [
            # English variations
            "hey pepper", "hi pepper", "hello pepper", "okay pepper", "ok pepper",
            "hey paper", "hi paper", "hello paper", "okay paper", "ok paper",
            "hey papper", "hi papper", "hello papper", "okay papper", "ok papper",
            "hey papa", "hi papa", "hello papa", "okay papa", "ok papa",
            "hey pepa", "hi pepa", "hello pepa", "hey peppa", "hey peper",
            "hey piper", "hey pipper", "hey pepe", "hey peppar",
            "a]y pepper", "hay pepper", "he pepper",
            # German variations
            "hallo pepper", "hallo paper", "hallo papper", "hallo papa",
            "hallo pepa", "hallo peppa", "hallo peper", "hallo piper",
            # Just "pepper" variants as fallback
            "pepper", "paper", "papper", "papa", "pepa", "peppa",
        ]
        
        # Timer for silence detection
        self.timer = self.create_timer(0.5, self.check_silence_timeout)
        
        self.get_logger().info(f"=== Whisper Transcriber Initialized ===")
        self.get_logger().info(f"  require_wake_word = {self.require_wake_word}")
        self.get_logger().info(f"  state = {self.state}")
        self.get_logger().info(f"  wake_words count = {len(self.wake_words)}")

    def load_whisper(self, model_size: str):
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
        self.get_logger().info(f"Loading Whisper '{model_size}' on {device_str}...")
        return whisper.load_model(model_size, device=device_str)

    def transcribe_file(self, path: str, lang: str | None) -> str:
        try:
            if not os.path.exists(path):
                return ""

            file_size = os.path.getsize(path)
            if file_size < 1000:
                return ""

            try:
                import librosa
                audio_data, sr = librosa.load(path, sr=16000)
                duration = len(audio_data) / sr
                rms = np.sqrt(np.mean(audio_data**2))

                if duration < 0.5 or rms < 0.001:
                    return ""
            except Exception:
                pass

            result = self.model.transcribe(
                path,
                language=lang,
                fp16=False,
                verbose=False
            )

            text = (result.get("text") or "").strip()
            return text

        except Exception as e:
            self.get_logger().error(f"Transcription error: {e}")
            return ""

    def find_wake_word(self, text: str):
        """Find wake word in text. Returns (wake_word, index) or (None, -1)"""
        text_clean = text.lower().strip()
        # Remove punctuation
        for char in ".,!?;:'\"":
            text_clean = text_clean.replace(char, "")
        
        # Sort wake words by length (longest first) to match "hallo pepper" before "pepper"
        sorted_wake_words = sorted(self.wake_words, key=len, reverse=True)
        
        for w in sorted_wake_words:
            if w in text_clean:
                return w, text_clean.find(w)
        return None, -1

    def check_silence_timeout(self):
        if self.state == "LISTENING" and self.question_buffer.strip():
            elapsed = time.time() - self.last_audio_time
            if elapsed > self.silence_timeout:
                self.get_logger().info(f"⏱️ Silence timeout ({elapsed:.1f}s) → publishing")
                self.publish_question()

    def audio_callback(self, msg):
        audio_path = msg.data
        lang_param = self.get_parameter('lang').get_parameter_value().string_value
        lang = None if lang_param.lower() == "none" else lang_param

        text = self.transcribe_file(audio_path, lang)

        if text:
            self.get_logger().info(f"📝 Transcribed: '{text}' [state={self.state}]")
            self.last_audio_time = time.time()

        # ========== MODE 1: NO WAKE WORD ==========
        if not self.require_wake_word:
            if text.strip():
                self.get_logger().info(f"✅ PUBLISHED (direct): '{text}'")
                self.pub_transcript.publish(String(data=text.strip()))
            return

        # ========== MODE 2: WAKE WORD REQUIRED ==========
        if self.state == "IDLE":
            wake_word, idx = self.find_wake_word(text)
            if wake_word:
                self.get_logger().info(f"🌟 Wake word '{wake_word}' detected!")
                self.state = "LISTENING"
                
                # Extract text after wake word from ORIGINAL text
                text_lower = text.lower()
                # Remove punctuation for finding
                text_lower_clean = text_lower
                for char in ".,!?;:'\"":
                    text_lower_clean = text_lower_clean.replace(char, "")
                
                idx_original = text_lower_clean.find(wake_word)
                if idx_original >= 0:
                    after_wake = text[idx_original + len(wake_word):].strip()
                    after_wake = after_wake.lstrip(".,!? ")
                else:
                    after_wake = ""
                
                self.question_buffer = after_wake
                
                if after_wake:
                    self.get_logger().info(f"📋 Question buffer: '{self.question_buffer}'")
                else:
                    self.get_logger().info("🎤 Listening for question...")
                
                self.check_completion()
            else:
                if text.strip():
                    self.get_logger().debug(f"No wake word in: '{text}'")

        elif self.state == "LISTENING":
            if text:
                if self.question_buffer and not self.question_buffer.endswith(" "):
                    self.question_buffer += " "
                self.question_buffer += text.strip()
                self.get_logger().info(f"📋 Question buffer: '{self.question_buffer}'")
                self.check_completion()
            else:
                if len(self.question_buffer.strip()) > 5:
                    self.get_logger().info("Empty chunk → publishing")
                    self.publish_question()
                else:
                    self.get_logger().info("Empty chunk, buffer too short → IDLE")
                    self.state = "IDLE"
                    self.question_buffer = ""

    def check_completion(self):
        b = self.question_buffer.strip()
        if not b:
            return
        if b.endswith('?') or b.endswith('.') or b.endswith('!'):
            if len(b.split()) >= 3:
                self.get_logger().info("✓ Punctuation → complete")
                self.publish_question()

    def publish_question(self):
        final_text = self.question_buffer.strip()
        
        if final_text:
            self.get_logger().info(f"✅ PUBLISHED: '{final_text}'")
            self.pub_transcript.publish(String(data=final_text))
        
        self.state = "IDLE" if self.require_wake_word else "DIRECT"
        self.question_buffer = ""


def main(args=None):
    rclpy.init(args=args)
    node = WhisperTranscriberNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
