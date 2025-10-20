#include <WiFi.h>                //mandatory libraries
#include <WebServer.h>
#include <Adafruit_GFX.h> 
#include <Adafruit_SSD1306.h>
#include <Wire.h>

// --- WiFi Configuration ---
const char* ssid = "********"; //connect to same wifi
const char* password = "*********";

// --- OLED Configuration ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

// --- I2C Pins ---
#define SDA_PIN 21
#define SCL_PIN 22

// --- Buzzer Pin ---
#define BUZZER_PIN 15  // Connect piezo buzzer signal pin here

// --- Crowd Count ---
volatile int currentCrowdCount = 0;
const int CROWD_THRESHOLD = 5;

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
WebServer server(80);

// --- Function Prototypes ---
void displayCount();
void handleRoot();
void handleUpdateCount();
void connectToWiFi();
void triggerBuzzer(bool on);

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);  // Ensure buzzer is off

  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed."));
    for (;;);
  }

  connectToWiFi();

  server.on("/", HTTP_GET, handleRoot);
  server.on("/update-count", HTTP_POST, handleUpdateCount);
  server.begin();

  Serial.println("HTTP Server started on port 80");
  displayCount();
}

void loop() {
  server.handleClient();
}

// --- Display + Buzzer ---
void displayCount() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);

  display.print("Crowd Detector:ONLINE");
  display.print("---------------------");

  display.setTextSize(2);
  display.setCursor(0, 30);
  display.print("COUNT: ");
  display.println(currentCrowdCount);

  if (currentCrowdCount > CROWD_THRESHOLD) {
    display.setTextSize(1);
    display.setCursor(0, 55);
    display.print("⚠️ CROWD WARNING!");  //will apppear in oled display
    Serial.println("⚠️ Crowd threshold exceeded!"); //will appear in serial monitor
    triggerBuzzer(true);
  } else {
    triggerBuzzer(false);
  }

  display.display();
}

// --- Web Server Handlers ---
void handleRoot() {
  String html = "<html><body>";
  html += "<h1>ESP32 Crowd Counter Server</h1>";
  html += "<p>Status: Listening for POST requests on /update-count</p>";
  html += "<p>Current Count: " + String(currentCrowdCount) + "</p>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleUpdateCount() {
  if (server.method() == HTTP_POST) {
    if (server.hasArg("plain")) {
      String countStr = server.arg("plain");
      int newCount = countStr.toInt();

      if (newCount >= 0) {
        currentCrowdCount = newCount;
        displayCount();
        Serial.print("New Crowd Count Received: ");
        Serial.println(currentCrowdCount);
        server.send(200, "text/plain", "Count received successfully.");
      } else {
        server.send(400, "text/plain", "Invalid count format.");
      }
    } else {
      server.send(400, "text/plain", "Missing data in request body.");
    }
  } else {
    server.send(405, "text/plain", "Method Not Allowed");
  }
}

// --- WiFi Connection ---
void connectToWiFi() {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.print("Connecting to: ");
  display.println(ssid);
  display.display();

  WiFi.begin(ssid, password);
  unsigned long startAttemptTime = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 15000) {
    delay(500);
    Serial.print(".");
    display.print(".");
    display.display();
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed.");
  }
}

// --- Buzzer Control ---
void triggerBuzzer(bool on) {
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
}
