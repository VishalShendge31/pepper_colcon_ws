# -*- coding: utf-8 -*-

from __future__ import print_function
import socket
import time
import struct
import threading
import sys
import base64
import os
import urllib
import urllib2
from naoqi import ALProxy

# ====== CONFIGURATION ======

ROBOT_IP = "10.219.165.53"
ROBOT_PORT = 9559
HOST_PC_IP = "10.219.165.184"
TTS_PORT = 5005
RECORD_SECONDS = 3  # Chunk size for continuous listening
AUDIO_FILE = "/home/nao/recorded_audio_stream.wav"

# ====== UI STATUS TEXTS ======

STATUS_IDLE = "Listening..."
STATUS_SPEAKING = "Speaking..."

# ====== TRACKING STATE ======

tts_playing = threading.Event()  # Signal when TTS is active
tts_lock = threading.Lock()      # Synchronization lock
tracking_active = threading.Event()

# ====== PROXIES ======

memory = ALProxy("ALMemory", ROBOT_IP, ROBOT_PORT)
recorder = ALProxy("ALAudioRecorder", ROBOT_IP, ROBOT_PORT)
player = ALProxy("ALAudioPlayer", ROBOT_IP, ROBOT_PORT)
tracker = ALProxy("ALTracker", ROBOT_IP, ROBOT_PORT)
motion = ALProxy("ALMotion", ROBOT_IP, ROBOT_PORT)
tablet = ALProxy("ALTabletService", ROBOT_IP, ROBOT_PORT)
battery_proxy = ALProxy("ALBattery", ROBOT_IP, ROBOT_PORT)

# ====== BATTERY POLLING ======

def battery_updater():
    while True:
        try:
            charge = battery_proxy.getBatteryCharge()
            url = "http://{}:5000/battery".format(HOST_PC_IP)
            data = urllib.urlencode({'battery': charge})
            req = urllib2.Request(url, data=data)
            urllib2.urlopen(req, timeout=3)
        except Exception as e:
            pass  # Fail semi-silently to not spam console
        time.sleep(30)

bat_thread = threading.Thread(target=battery_updater)
bat_thread.setDaemon(True)
bat_thread.start()

# ====== WAKE-UP KEEPER (prevent Pepper from sleeping) ======

def wake_up_keeper():
    """Call ALMotion.wakeUp() every 2 minutes to prevent Pepper from going to sleep."""
    while True:
        try:
            motion.wakeUp()
            print("[WakeUp] ALMotion.wakeUp() called - Pepper kept awake")
        except Exception as e:
            print("[WakeUp] Error calling wakeUp: {}".format(e))
        time.sleep(120)  # Wait 2 minutes before next call

wakeup_thread = threading.Thread(target=wake_up_keeper)
wakeup_thread.setDaemon(True)
wakeup_thread.start()

# ====== TABLET DISPLAY ======

def show_tablet_message(message_text, bg_color="#101318", fg_color="#FFFFFF"):
    try:
        # Instead of pushing a huge string to the legacy tablet, we stream the Jetson UI
        tablet.showWebview("http://{}:5000/".format(HOST_PC_IP))
    except Exception as e:
        print("Tablet display error: {}".format(e))

def set_status_idle():
    pass

def set_status_speaking():
    pass

# ====== TRACKING FUNCTIONS ======

def start_general_tracking():
    try:
        tracker.registerTarget("People", 2.0)
        tracker.track("People")
        tracking_active.set()
        print("Started general human tracking")
    except Exception as e:
        print("Error starting general tracking: {}".format(e))

def stop_tracking():
    try:
        if tracking_active.is_set():
            tracker.stopTracker()
            tracker.unregisterAllTargets()
            motion.angleInterpolation(["HeadYaw", "HeadPitch"], [0.0, 0.0], 2.0, True)
            tracking_active.clear()
            print("Stopped tracking and reset head position")
    except Exception as e:
        print("Error stopping tracking: {}".format(e))

# ====== TCP SETUP FOR AUDIO SENDING ======

audio_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
while not connected:
    try:
        audio_sock.connect((HOST_PC_IP, 5005))
        print("Connected to host PC at {}:5005".format(HOST_PC_IP))
        connected = True
    except socket.error as e:
        print("Waiting for host PC on {}:{} ...".format(HOST_PC_IP, 5005))
        time.sleep(2)

# ====== TCP SERVER FOR TTS AUDIO ======

tts_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tts_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tts_sock.bind((ROBOT_IP, TTS_PORT))
tts_sock.listen(1)
print("TTS server listening on port {}...".format(TTS_PORT))

def recv_all(sock, size):
    data = b""
    while len(data) < size:
        packet = sock.recv(min(4096, size - len(data)))
        if not packet:
            return None
        data += packet
    return data

def tts_server():
    while True:
        try:
            conn, addr = tts_sock.accept()
            print("Connected by {} for TTS".format(addr))
            try:
                while True:
                    size_bytes = recv_all(conn, 8)
                    if not size_bytes:
                        break
                    audio_size = struct.unpack(">Q", size_bytes)[0]
                    print("Receiving {} bytes of TTS audio".format(audio_size))

                    audio_data = recv_all(conn, audio_size)
                    if not audio_data:
                        break

                    tts_file = "/home/nao/tts_output.wav"
                    with open(tts_file, "wb") as f:
                        f.write(audio_data)

                    with tts_lock:
                        tts_playing.set()
                        set_status_speaking()
                        start_general_tracking()
                        
                        try:
                            # Stop current mic recording to prevent loopback
                            recorder.stopMicrophonesRecording()
                        except:
                            pass

                    print("Playing TTS audio...")
                    try:
                        player.playFile(tts_file)
                        time.sleep(0.5)
                    except Exception as e:
                        print("Error playing TTS audio: {}".format(e))

                    with tts_lock:
                        tts_playing.clear()
                        stop_tracking()
                        set_status_idle()
                        print("TTS completed, resuming listening stream...")

            finally:
                with tts_lock:
                    tts_playing.clear()
                    stop_tracking()
                try:
                    conn.close()
                except:
                    pass
                set_status_idle()
                
        except Exception as e:
            print("TTS server error: {}".format(e))
            with tts_lock:
                tts_playing.clear()
                stop_tracking()
            set_status_idle()

tts_thread = threading.Thread(target=tts_server)
tts_thread.setDaemon(True)
tts_thread.start()

# ====== MAIN CONTINUOUS AUDIO LOOP ======

set_status_idle()

# ====== OPEN DASHBOARD ON TABLET ======
try:
    tablet.showWebview("http://{}:5000/".format(HOST_PC_IP))
    print("Tablet now showing dashboard at http://{}:5000/".format(HOST_PC_IP))
except Exception as e:
    print("Could not open tablet webview: {}".format(e))

print("Starting continuous audio streamer...")
print("Chunk size: {} seconds".format(RECORD_SECONDS))

try:
    while True:
        if tts_playing.is_set():
            time.sleep(0.5)
            continue
            
        try:
            # 1. Catch cleanup from previous interrupted recordings
            try:
                recorder.stopMicrophonesRecording()
            except:
                pass

            # 2. Start recording chunk
            recorder.startMicrophonesRecording(AUDIO_FILE, "wav", 16000, [0, 0, 1, 0])
            time.sleep(RECORD_SECONDS)
            recorder.stopMicrophonesRecording()

            # Wait if TTS started while we were recording
            if tts_playing.is_set():
                continue

            # 3. Read and Send chunk to Jetson
            if not os.path.exists(AUDIO_FILE):
                continue

            with open(AUDIO_FILE, "rb") as f:
                audio_data = f.read()

            if len(audio_data) < 100:
                continue
            
            # Send standard packet: size (unsigned long long) + audio data
            audio_sock.sendall(struct.pack(">Q", len(audio_data)))
            audio_sock.sendall(audio_data)
            
        except socket.error as e:
            print("Connection to Jetson lost: {}".format(e))
            connected = False
            while not connected:
                print("Trying to reconnect to Jetson...")
                try:
                    audio_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    audio_sock.connect((HOST_PC_IP, 5005))
                    connected = True
                    print("Reconnected!")
                except:
                    time.sleep(2)
        except Exception as e:
            print("Recording stream error: {}".format(e))
            time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting...")
    try:
        recorder.stopMicrophonesRecording()
    except:
        pass
    with tts_lock:
        tts_playing.clear()
    stop_tracking()
    try:
        audio_sock.close()
    except:
        pass
    try:
        tts_sock.close()
    except:
        pass
    print("Cleanup completed")
