#!/usr/bin/env python3
import os
import time
import warnings
import torch
import whisper
import numpy as np
import io
# Suppress deprecation warnings from torchaudio used by silero-vad
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class WhisperTranscriberNode(Node):
    def __init__(self):
        super().__init__('whisper_transcriber')

        # Parameters
        self.declare_parameter('lang', 'None')
        self.declare_parameter('model', 'base')
        self.declare_parameter('require_wake_word', True)
        
        model_size = self.get_parameter('model').get_parameter_value().string_value
        self.require_wake_word = self.get_parameter('require_wake_word').get_parameter_value().bool_value

        self.model = self.load_whisper(model_size)
        self.vad_model = self.load_vad()

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

        # Hallucination Filter - common Whisper "ghost" outputs during silence
        self.junk_phrases = [
            "thanks for watching", "thank you for watching", "please subscribe",
            "you", "thank you", "watching", "subtitle by", "translated by",
            "sh", "s", "m", "h", "uh", "um"
        ]


    def load_whisper(self, model_size: str):
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
        self.get_logger().info(f"Loading Whisper '{model_size}' on {device_str}...")
        return whisper.load_model(model_size, device=device_str)

    def load_vad(self):
        """Load Silero VAD from the pip package (model bundled, no internet needed)."""
        try:
            from silero_vad import load_silero_vad
            self.get_logger().info("Loading Silero VAD from pip package...")
            vad_model = load_silero_vad()
            vad_model.eval()
            self.get_logger().info("Silero VAD loaded successfully (offline).")
            return vad_model
        except Exception as e:
            self.get_logger().warn(f"Could not load Silero VAD: {e}. Running without VAD.")
            return None

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

                # Stricter RMS Gate (0.01) to ignore silence/background hum
                if duration < 0.5 or rms < 0.01:
                    return ""

                # === Silero VAD Gate ===
                if self.vad_model is not None:
                    try:
                        from silero_vad import read_audio, get_speech_timestamps
                        audio_tensor = read_audio(path, sampling_rate=16000)
                        timestamps = get_speech_timestamps(audio_tensor, self.vad_model, sampling_rate=16000, threshold=0.45)
                        if not timestamps:
                            self.get_logger().debug("VAD: No speech detected, skipping Whisper.")
                            return ""
                    except Exception as vad_e:
                        self.get_logger().debug(f"VAD check failed: {vad_e}")
            except Exception:
                pass

            device_is_cuda = self.model.device.type == "cuda"

            # Use language=None for auto-detection (supports EN and DE simultaneously).
            # Whisper detects the language internally as part of transcription,
            # which is more accurate for short utterances than a separate detect_language pass.
            # If the user explicitly passed a lang param, respect that.
            transcribe_lang = lang  # None = auto-detect (handles EN+DE)

            result = self.model.transcribe(
                path,
                language=transcribe_lang,
                fp16=device_is_cuda,
                initial_prompt="Pepper.",     # Minimal spelling hint (avoids biasing transcription)
                temperature=0,               # Greedy decoding = less hallucination
                beam_size=5,                 # More thorough search
                condition_on_previous_text=False,  # Prevent old context from corrupting new audio
                no_speech_threshold=0.6,     # Skip chunk if model thinks it's mostly silence
                logprob_threshold=-1.0,      # Filter low-confidence text
                verbose=False
            )

            text = (result.get("text") or "").strip()
            
            # Junk Filter
            text_lower = text.lower().strip().rstrip(".,!?")
            if text_lower in self.junk_phrases:
                self.get_logger().debug(f"Filtered junk/hallucination: '{text}'")
                return ""
                
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
