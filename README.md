# VisionAlert 🚨

VisionAlert is a real-time crowd detection and alert system using ESP32-CAM for video streaming, YOLOv8 for people counting, and Twilio for SMS alerts. It displays the crowd count on the ESP32 and triggers a buzzer warning when the count exceeds a defined threshold.

## 🔧 Features
- Live video streaming via ESP32-CAM
- Crowd detection using YOLOv8 in Python
- SMS alerts via Twilio when crowd exceeds threshold
- Real-time count display on ESP32
- Buzzer warning for crowd overflow

## 🛠️ Hardware Used
- ESP32-CAM
- Buzzer
- Laptop (for Python processing)
- Optional: esp32,OLED display, PS4 controller, servo motor

## 🧠 Software Stack
- Python (OpenCV, Ultralytics YOLOv8, Twilio)
- Arduino IDE (ESP32 receiver code)
- Serial or HTTP communication between laptop and ESP32

## 📦 Setup Instructions

### 1. ESP32-CAM
- Flash with camera streaming code
- Connect to Wi-Fi and note the IP address

### 2. Python Script
- Install dependencies:
  ```bash
  pip install ultralytics opencv-python twilio
-Run crowd_detect_twilio.py:
- Connects to ESP32-CAM stream
- Uses YOLOv8 to count people
- Sends count to ESP32
- Sends SMS if count exceeds threshold

**###3. ESP32 Receiver**
- Receives count via serial or HTTP
- Displays count
- Activates buzzer if count > threshold

**📄 License**
This project is licensed under the MIT License. See the LICENSE file for details.

