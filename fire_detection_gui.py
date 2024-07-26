import cv2
import numpy as np
from ultralytics import YOLO
import threading
import time
import requests
from tkinter import *
from PIL import Image, ImageTk

# Load YOLOv8 model
model = YOLO('best.pt')  # Ganti dengan path ke model yang sudah dilatih

# Telegram configuration
CHAT_ID = "1297914757"  # Ganti dengan chat ID Anda
BOT_TOKEN = "7143582268:AAEKoe33bOQw1CdEmpCTXbvADILBh9kcF-4"  # Ganti dengan token bot Anda
notification_interval = 60  # Interval waktu dalam detik untuk mengirim notifikasi
last_notification_time = 0

# Initialize Tkinter
root = Tk()
root.title("ESP32-CAM Live Stream with Fire Detection")
root.geometry("640x480")

# Create a Label to display the video
video_label = Label(root)
video_label.pack()

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

def detect_fire(frame, current_time):
    global last_notification_time
    fire_detected = False
    results = model(frame)
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
    if fire_detected and (current_time - last_notification_time > notification_interval):
        send_telegram_notification("Fire Detected")
        last_notification_time = current_time  # Update waktu notifikasi terakhir
    return frame

def update_frame():
    url = "http://192.168.80.109:81/stream"  # Ganti dengan URL stream dari ESP32-CAM
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
            frame = cv2.resize(frame, (640, 480))
            current_time = time.time()
            frame = detect_fire(frame, current_time)
            # Convert the frame to ImageTk format
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = ImageTk.PhotoImage(image=img)
            video_label.imgtk = img
            video_label.configure(image=img)
        root.update()

# Run the update_frame function in a separate thread
thread = threading.Thread(target=update_frame)
thread.daemon = True
thread.start()

root.mainloop()
