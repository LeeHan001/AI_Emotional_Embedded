import socket 
import joblib # Read AI Model
import cv2 
import numpy as np
import mediapipe as mp
import time
import json 
import asyncio #Asynchronous
import websockets 
import threading 
from collections import deque #que
import statistics
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Set IP, PORT Number
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
WS_PORT = 8080

# Pakcet for send to Unity
packet_data = {
    "FaceCheck": False,
    "Probability": 0.0,
    "FaceValue": 0,
    "FaceName": "None",
    "DayNightCheck": True,
    "DayNightName" : "Day",
}

# Maping Number
EMOTION_TO_ID = {
    "Neutral": 0, "Happy": 1, "Anger": 2, "Sad": 3,
    "Surprise": 4, "Sleep": 5, "Pouting": 6, "Suspicious": 7, "None": 0
}

# Load AI Model
try:
    LabelEncoder = joblib.load('LabelEncoder3.pkl')
    Model = joblib.load('RandomForest3.pkl')
except Exception as e:
    print(f"fail load AI Model: {e}")

# MediaPipe setting
base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,
    num_faces=1
)
detector = vision.FaceLandmarker.create_from_options(options)

TARGET_BLENDSHAPES = [
    'browDownLeft', 'browDownRight', 'browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 
    'eyeSquintLeft', 'eyeSquintRight', 'eyeWideLeft', 'eyeWideRight', 'jawOpen', 
    'mouthFrownLeft', 'mouthFrownRight', 'mouthPressLeft', 'mouthPressRight', 'mouthPucker', 
    'mouthSmileLeft', 'mouthSmileRight', 'mouthStretchLeft', 'mouthStretchRight', 
    'noseSneerLeft', 'noseSneerRight'
]

# UDP Socket setting
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Websocket (Asynchronous function)
async def send_face_data(websocket):
    print(f"Unity Connected: {websocket.remote_address}")
    try:
        while True:
            await websocket.send(json.dumps(packet_data))
            await asyncio.sleep(0.05) # 20 FPS Sending
    except websockets.ConnectionClosed:
        print("Unity Disconnected")

# Maim
async def main():
    print(f"Status: Receiver is running on UDP {UDP_PORT}")
    
    # Start Websocket
    server = await websockets.serve(send_face_data, "0.0.0.0", WS_PORT)
    print(f"WebSocket Server initialized on port {WS_PORT}")

    # Timer and Que 
    blink_start_time = None
    window_size = 15
    emotion_history = deque(maxlen=window_size)
    prob_history = deque(maxlen=window_size)

    while True:
        # Get Data from UDP 
        data, addr = sock.recvfrom(65507) 
        nparr = np.frombuffer(data, np.uint8) 
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR) 
        
        if frame is None:
            continue

        # MediaPipe 
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        detection_result = detector.detect(mp_image)
        
        raw_emotion = "None"
        raw_confidence = 0.0
        face_check = False

        if detection_result.face_blendshapes:
            face_check = True
            shapes = detection_result.face_blendshapes[0]
            shape_dict = {s.category_name: s.score for s in shapes}
        
            # --- Rule-Based Logic ---
            # Sleep (Check 2Seconds)
            is_blinking = shape_dict.get('eyeBlinkLeft', 0) > 0.8 and shape_dict.get('eyeBlinkRight', 0) > 0.8
            if is_blinking:
                if blink_start_time is None:
                    blink_start_time = time.time()
                elapsed = time.time() - blink_start_time
                if elapsed >= 2.0:
                    raw_emotion = "Sleep"
                    raw_confidence = (shape_dict.get('eyeBlinkLeft', 0) + shape_dict.get('eyeBlinkRight', 0)) / 2
                else:
                    raw_emotion = "Neutral" # 2초 전까지는 무표정 유지
            else:
                blink_start_time = None
                
                # Pouting
                if shape_dict.get('cheekPuff', 0) > 0.95 or shape_dict.get('mouthPucker', 0) > 0.95:
                    raw_emotion = "Pouting"
                    raw_confidence = max(shape_dict.get('cheekPuff', 0), shape_dict.get('mouthPucker', 0))
                # Suspicious
                elif (shape_dict.get('eyeSquintLeft', 0) + shape_dict.get('eyeSquintRight', 0)) / 2 > 0.7:
                    if (shape_dict.get('mouthSmileLeft', 0) + shape_dict.get('mouthSmileRight', 0)) / 2 < 0.2:
                        raw_emotion = "Suspicious"
                        raw_confidence = (shape_dict['eyeSquintLeft'] + shape_dict['eyeSquintRight']) / 2

                # AI Model (Random Forest)
                if raw_emotion == "None" or raw_emotion == "Neutral":
                    input_features = [shape_dict.get(name, 0.0) for name in TARGET_BLENDSHAPES]
                    input_array = np.array([input_features])
                    probabilities = Model.predict_proba(input_array)[0]
                    max_idx = np.argmax(probabilities)
                    raw_emotion = LabelEncoder.inverse_transform([max_idx])[0]
                    raw_confidence = probabilities[max_idx]

        # moving average filter (Smoothing)
        if face_check:
            emotion_history.append(raw_emotion)
            prob_history.append(raw_confidence)
            
            # Check the most detected expression
            final_emotion = statistics.mode(emotion_history)
            
            # Calculate Prob
            matched_probs = [p for e, p in zip(emotion_history, prob_history) if e == final_emotion]
            final_confidence = sum(matched_probs) / len(matched_probs)
        else:
            emotion_history.clear()
            prob_history.clear()
            final_emotion = "None"
            final_confidence = 0.0

        # Update Packet
        packet_data['FaceCheck'] = face_check
        packet_data['Probability'] = round(float(final_confidence), 2)
        packet_data['FaceName'] = final_emotion
        packet_data['FaceValue'] = EMOTION_TO_ID.get(final_emotion, 0)

        # UI visible
        display_color = (0, 255, 0) if face_check else (0, 0, 255)
        status_text = f"{final_emotion} ({final_confidence*100:.1f}%)" if face_check else "No Face"
        cv2.putText(img_rgb, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, display_color, 2)
        
        cv2.imshow('Emotion Streaming Server', img_rgb)
        
        # asynchronous loop
        await asyncio.sleep(0.001)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    sock.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer Shutdown.")