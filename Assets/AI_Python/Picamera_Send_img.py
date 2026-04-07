import socket
import cv2
import numpy as np
from picamera2 import Picamera2

# Setting
UDP_IP = "127.0.0.1" # For Local Access
UDP_PORT = 5005 # UDP PORT NUMBER : 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#AF_INET : Internt,Network / SOCK_DGRAM : UDP -> AF_UNIX : UNIX DOMAIN / SOCK_STREAM : TCP

picam2 = Picamera2()  # Initialize picamera2 640x480 RGB formart
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(config)
picam2.start()

print("send image")

try:
    while True:
        # Capture image
        img = picam2.capture_array()
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # JPEG Compression (for UDP Communication)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
        result, encoded_img = cv2.imencode('.jpg', img_bgr, encode_param)

        if result:
            # Convert encoded
            data = np.array(encoded_img)
            stringData = data.tobytes() #image to byte

            # Check Packet Size (Must be < 65,507 bytes for UDP)
            if len(stringData) < 65507:
                sock.sendto(stringData, (UDP_IP, UDP_PORT))
            else:
                print(f"Warning: Packet too large! ({len(byte_data)} bytes)")

except KeyboardInterrupt:
    picam2.stop()
    sock.close()