import cv2
import requests
import time
from ultralytics import YOLO
from twilio.rest import Client  # ✅ Twilio for SMS

# --- ESP32 Configuration ---
ESP32_IP = "10.165.80.***"
ESP32_PORT = 80
ENDPOINT = "/update-count"
API_URL = f"http://{ESP32_IP}:{ESP32_PORT}{ENDPOINT}"

# --- YOLOv8 Setup ---
MODEL_PATH = 'yolov8n.pt'
model = YOLO(MODEL_PATH)
PERSON_CLASS_ID = 0
CONFIDENCE_THRESHOLD = 0.5

# --- Video Source ---
VIDEO_SOURCE = 0
cap = cv2.VideoCapture(VIDEO_SOURCE)
if not cap.isOpened():
    print(f"Error: Could not open video source {VIDEO_SOURCE}.")
    exit()

# --- Throttle Settings ---
SEND_INTERVAL_SECONDS = 1.0
last_send_time = time.time()

# --- Crowd Threshold for SMS Alert ---
CROWD_SMS_THRESHOLD = 5  # ✅ Send SMS when count > 5
last_sms_time = 0
SMS_INTERVAL_SECONDS = 60  # Avoid spamming

# --- Twilio SMS Setup --- set up ur own twilio acc and change the credentials below
TWILIO_SID = "---------------------"
TWILIO_AUTH_TOKEN = "------------------------"
TWILIO_PHONE = "+*************"       # Your Twilio number
TARGET_PHONE = "+91*********"      # Your verified number

twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def send_sms_alert(count):
    global last_sms_time
    now = time.time()
    if now - last_sms_time < SMS_INTERVAL_SECONDS:
        return

    message = f"⚠️ Crowd Alert: {count} people detected!"
    try:
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=TARGET_PHONE
        )
        print(f"[{time.strftime('%H:%M:%S')}] 📱 SMS sent: {message}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ SMS failed: {e}")
    finally:
        last_sms_time = now  # ✅ Always update to avoid retry loop

def send_count_to_esp32(count):
    global last_send_time
    current_time = time.time()
    if current_time - last_send_time < SEND_INTERVAL_SECONDS:
        return

    try:
        payload = str(count)
        headers = {'Content-Type': 'text/plain'}
        response = requests.post(API_URL, data=payload, headers=headers, timeout=0.5)
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] Count Sent: {count}. Status: OK.")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ESP32 returned status code {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"[{time.strftime('%H:%M:%S')}] Timeout connecting to ESP32.")
    except requests.exceptions.ConnectionError:
        print(f"[{time.strftime('%H:%M:%S')}] Connection error to ESP32.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Unexpected error: {e}")

    last_send_time = current_time

print(f"--- Crowd Detection Running. Target ESP32: {API_URL} ---")

while True:
    ret, frame = cap.read()
    if not ret:
        print("End of video stream or error reading frame.")
        break

    results = model(frame, classes=[PERSON_CLASS_ID], conf=CONFIDENCE_THRESHOLD, verbose=False)
    crowd_count = len(results[0].boxes) if results and results[0].boxes else 0

    annotated_frame = results[0].plot()
    cv2.putText(annotated_frame, f'Crowd Count: {crowd_count}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow('YOLOv8 Crowd Detector', annotated_frame)

    send_count_to_esp32(crowd_count)

    if crowd_count > CROWD_SMS_THRESHOLD:
        print(f"[{time.strftime('%H:%M:%S')}] 🚨 Crowd count {crowd_count} exceeds threshold {CROWD_SMS_THRESHOLD}")
        send_sms_alert(crowd_count)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
