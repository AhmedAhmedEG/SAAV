#include <TinyGPSPlus.h>
#include <SoftwareSerial.h>

// You have to place ublox neo-6 gps module outdoors or near a window and wait until it starts blinking, thus indicating it has found a position fix aka enought amount of GPS satellites, then you will see output from this code.
// If you are using ESP8266, never connect the RX & Tx pins of the neo-6 to the Rx & Tx of the ESP, as it will diconnect the ESP's USB from the serial connection.
// And you will never see any output other than the data neo-6 spits out in the UART connection.
// gpsSerial arguments are (Tx_pin, Rx_pin)
SoftwareSerial gpsSerial(5, 4);
TinyGPSPlus gps;

void setup()
{
  Serial.begin(9600);
  gpsSerial.begin(9600);
}

void loop() {

  while (gpsSerial.available() > 0) {
    // UART buffer sends data in 8-bit batches, you have to cast every 8-bits to char and collect them in an array to get the full message.
    // This .encode function casts the bits to chars and collects them for you, and it will return true only if the message it has collected is valid.
    // The collected message will only be valid if the ublox neo-6 gps module is blinking.
    if (gps.encode(gpsSerial.read())) {

      if (gps.location.isValid()) {
        Serial.print(F("Location: ")); 
        Serial.print(gps.location.lat(), 6);
        Serial.print(F(","));
        Serial.println(gps.location.lng(), 6);
      }

    }

  }

}