import joblib
import cv2
import numpy as np
import mediapipe as mp
import time
import json
import asyncio
import websockets
from collections import deque
import statistics
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ========= Settings =========
WS_PORT = 8080
CAM_INDEX = 0          # 기본 웹캠: 0 (다른 카메라면 1,2...)
SEND_WS = True         # Unity/WebGL로 보내려면 True, 아니면 False
WINDOW_SIZE = 15       # smoothing window
SLEEP_SECONDS = 2.0    # 눈 감은 상태 지속 시간

# Packet for Unity
packet_data = {
    "FaceCheck": False,
    "Probability": 0.0,
    "FaceValue": 0,
    "FaceName": "None",
    "DayNightCheck": True,
    "DayNightName": "Day",
}

EMOTION_TO_ID = {
    "Neutral": 0, "Happy": 1, "Anger": 2, "Sad": 3,
    "Surprise": 4, "Sleep": 5, "Pouting": 6, "Suspicious": 7, "None": 0
}

# ========= Load AI Model =========
try:
    LabelEncoder = joblib.load("LabelEncoder3.pkl")
    Model = joblib.load("RandomForest3.pkl")
except Exception as e:
    raise RuntimeError(f"fail load AI Model: {e}")

# ========= MediaPipe =========
base_options = python.BaseOptions(model_asset_path="face_landmarker.task")
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,
    num_faces=1
)
detector = vision.FaceLandmarker.create_from_options(options)

TARGET_BLENDSHAPES = [
    "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    "eyeSquintLeft", "eyeSquintRight", "eyeWideLeft", "eyeWideRight", "jawOpen",
    "mouthFrownLeft", "mouthFrownRight", "mouthPressLeft", "mouthPressRight", "mouthPucker",
    "mouthSmileLeft", "mouthSmileRight", "mouthStretchLeft", "mouthStretchRight",
    "noseSneerLeft", "noseSneerRight"
]

# ========= WebSocket =========
async def send_face_data(websocket):
    print(f"Unity Connected: {websocket.remote_address}")
    try:
        while True:
            await websocket.send(json.dumps(packet_data))
            await asyncio.sleep(0.05)  # 20 FPS
    except websockets.ConnectionClosed:
        print("Unity Disconnected")

# ========= Main =========
async def main():
    # Start WebSocket server (optional)
    server = None
    if SEND_WS:
        server = await websockets.serve(send_face_data, "0.0.0.0", WS_PORT)
        print(f"WebSocket Server initialized on port {WS_PORT}")

    # OpenCV Camera
    cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {CAM_INDEX}")

    # (선택) 해상도 설정
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    blink_start_time = None
    emotion_history = deque(maxlen=WINDOW_SIZE)
    prob_history = deque(maxlen=WINDOW_SIZE)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        # MediaPipe expects RGB
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

            # ---- Rule-Based Logic ----
            is_blinking = shape_dict.get("eyeBlinkLeft", 0) > 0.8 and shape_dict.get("eyeBlinkRight", 0) > 0.8
            if is_blinking:
                if blink_start_time is None:
                    blink_start_time = time.time()
                elapsed = time.time() - blink_start_time
                if elapsed >= SLEEP_SECONDS:
                    raw_emotion = "Sleep"
                    raw_confidence = (shape_dict.get("eyeBlinkLeft", 0) + shape_dict.get("eyeBlinkRight", 0)) / 2
                else:
                    raw_emotion = "Neutral"  # SLEEP_SECONDS 전까지는 Neutral 처리
                    raw_confidence = 0.0
            else:
                blink_start_time = None

                # Pouting
                if shape_dict.get("cheekPuff", 0) > 0.95 or shape_dict.get("mouthPucker", 0) > 0.95:
                    raw_emotion = "Pouting"
                    raw_confidence = max(shape_dict.get("cheekPuff", 0), shape_dict.get("mouthPucker", 0))

                # Suspicious
                elif (shape_dict.get("eyeSquintLeft", 0) + shape_dict.get("eyeSquintRight", 0)) / 2 > 0.7:
                    if (shape_dict.get("mouthSmileLeft", 0) + shape_dict.get("mouthSmileRight", 0)) / 2 < 0.2:
                        raw_emotion = "Suspicious"
                        raw_confidence = (shape_dict.get("eyeSquintLeft", 0) + shape_dict.get("eyeSquintRight", 0)) / 2

                # AI Model (RandomForest)
                if raw_emotion == "None" or raw_emotion == "Neutral":
                    input_features = [shape_dict.get(name, 0.0) for name in TARGET_BLENDSHAPES]
                    input_array = np.array([input_features], dtype=np.float32)
                    probabilities = Model.predict_proba(input_array)[0]
                    max_idx = int(np.argmax(probabilities))
                    raw_emotion = LabelEncoder.inverse_transform([max_idx])[0]
                    raw_confidence = float(probabilities[max_idx])

        # ---- Smoothing (mode + mean prob) ----
        if face_check:
            emotion_history.append(raw_emotion)
            prob_history.append(raw_confidence)

            try:
                final_emotion = statistics.mode(emotion_history)
            except statistics.StatisticsError:
                # 동률이면 최근값 우선
                final_emotion = emotion_history[-1]

            matched_probs = [p for e, p in zip(emotion_history, prob_history) if e == final_emotion]
            final_confidence = sum(matched_probs) / len(matched_probs) if matched_probs else 0.0
        else:
            emotion_history.clear()
            prob_history.clear()
            final_emotion = "None"
            final_confidence = 0.0

        # Update packet
        packet_data["FaceCheck"] = face_check
        packet_data["Probability"] = round(float(final_confidence), 2)
        packet_data["FaceName"] = final_emotion
        packet_data["FaceValue"] = EMOTION_TO_ID.get(final_emotion, 0)

        # UI Visible (OpenCV window)
        status_text = f"{final_emotion} ({final_confidence*100:.1f}%)" if face_check else "No Face"
        cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if face_check else (0, 0, 255), 2)
        cv2.imshow("Emotion (PC Camera)", frame)

        # Exit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        await asyncio.sleep(0.001)

    cap.release()
    cv2.destroyAllWindows()
    if server is not None:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer Shutdown.")