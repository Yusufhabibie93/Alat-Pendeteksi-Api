import cv2
from ultralytics import YOLO

# Load YOLOv8 model
model = YOLO('best.pt')  # Ganti dengan path ke model yang sudah dilatih

# Load test image
image_path = 'dataset/test/images/fire3_jpg.rf.8058077e9c73fa110127ee5a43521b06.jpg'  # Ganti dengan path ke gambar uji
image = cv2.imread(image_path)

# Perform detection
results = model(image)

# Draw bounding boxes
for result in results:
    boxes = result.boxes
    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = box.conf[0]
        cls = box.cls[0]
        if cls == 0:  # Assuming 'fire' is class 0
            label = f"Fire {conf:.2f}"
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

# Display the image
cv2.imshow("Detection", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
