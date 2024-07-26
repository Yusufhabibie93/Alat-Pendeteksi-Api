from flask import Flask, render_template, Response
import cv2
import numpy as np
from ultralytics import YOLO
import threading
import queue
import requests
import time
from datetime import datetime
import os

image_path = "/firedetection/"
# Load YOLOv8 model
model = YOLO('best.pt')  # Ganti dengan path ke model yang sudah dilatih

app = Flask(__name__)

frame_queue = queue.Queue(maxsize=10)
result_frame = None
lock = threading.Lock()

# Telegram configuration
CHAT_ID = "1297914757"  # Ganti dengan chat ID Anda
BOT_TOKEN = "7143582268:AAEKoe33bOQw1CdEmpCTXbvADILBh9kcF-4"  # Ganti dengan token bot Anda
notification_interval = 60  # Interval waktu dalam detik untuk mengirim notifikasi
last_notification_time = 0

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Telegram message sent successfully")
        else:
            print(f"Failed to send message: {response.status_code}")
    except Exception as e:
        print(f"Error sending message: {e}")

def send_telegram_notif_photo(foto):
    data = {"chat_id": CHAT_ID, "caption": "Deteksi Kebakaran"}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto?chat_id={CHAT_ID}"
    with open(foto, "rb") as image_file:
        ret = requests.post(url, data=data, files={"photo": image_file})
    try:
        if ret.status_code == 200:
            print("Telegram photo sent successfully")
        else:
            print(f"Failed to send photo: {ret.status_code}")
    except Exception as e:
        print(f"Error sending photo: {e}")
    return ret.json()

def detect_fire():
    global result_frame, last_notification_time
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            results = model(frame)
            fire_detected = False
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0]
                    cls = box.cls[0]
                    if cls == 0:  # Assuming 'fire' is class 0
                        label = f"Fire {conf:.2f}"
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        print(f"Detected {label} at ({x1}, {y1}, {x2}, {y2}) with confidence {conf:.2f}")
                        fire_detected = True
                       
            if fire_detected and (time.time() - last_notification_time > notification_interval):
                now = datetime.now()
                string = now.strftime('%Y%m%d%H%M%S')
                simpanimg = os.path.join(string +'.jpg')
                cv2.imwrite(simpanimg, frame)
                send_telegram_notification("Peringatan: Aktivitas api terdeteksi. Harap periksa dan pastikan area tersebut aman.")
                send_telegram_notif_photo(simpanimg)
                last_notification_time = time.time()
            with lock:
                result_frame = frame

def gen_frames():
    url = "URL STREAM"  # Ganti dengan URL stream dari ESP32-CAM
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("Error: Unable to open video stream")
        return
    while True:
        success, frame = cap.read()
        if not success:
            print("Error: Failed to grab frame")
            break
        else:
            frame = cv2.resize(frame, (320, 240))
            if frame_queue.empty():  # Only put frame if queue is empty
                frame_queue.put(frame)
            with lock:
                if result_frame is not None:
                    ret, buffer = cv2.imencode('.jpg', result_frame)
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    detection_thread = threading.Thread(target=detect_fire)
    detection_thread.daemon = True
    detection_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True)
