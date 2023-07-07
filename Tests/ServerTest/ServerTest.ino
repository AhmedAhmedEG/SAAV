#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

ESP8266WebServer server(80);

void setup() {
  Serial.begin(9600);

  WiFi.begin("Ahmed 2.4GHz", "Rush1-Up2-To3-Go4");

  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  Serial.print("Connected, IP address: ");
  Serial.println(WiFi.localIP());

  server.on("/control", controlHandle);
  server.on("/gps", gpsHandle);
  server.begin();
}

void loop() {
  server.handleClient();
}

void controlHandle() {
    String command = server.arg("plain");
    
    StaticJsonDocument<256> doc;
    deserializeJson(doc, command);

    long angle = doc["angle"];
    long speed = doc["speed"];

    avoid = doc["avoidance"];

    server.send(200, "text/plain", "ok");
}

void gpsHandle() {
    StaticJsonDocument<256> doc;

    doc["lat"];
    doc["log"];

    String res;
    serializeJson(doc, res);

    server.send(200, "postion/json", res);
}