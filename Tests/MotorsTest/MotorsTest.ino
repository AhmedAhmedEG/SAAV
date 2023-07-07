#include <Adafruit_PWMServoDriver.h>

#define SERVO_FREQ 50
#define SERVO_CH 15
#define ESC_CH 14

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

void setup() {
  Serial.begin(115200);

  pwm.begin();
  pwm.setPWMFreq(SERVO_FREQ);

  delay(10);
}

void loop() {

  while (Serial.available()) {
    String m = Serial.readString();
    m = m.substring(0, m.length() - 1);

    if (m == "f") { moveForward(); }
    else if (m == "b") { moveBackward(); }
    else if (m == "l") { turnLeft(); }
    else if (m == "r") { turnRight(); }
    else if (m == "s") { stop(); }
    else {
      String c = m.substring(0, 1);
      String v = m.substring(1);
      
      if (c == "s") { pwm.setPWM(SERVO_CH, 0, v.toInt()); }
      else if (c == "e") { pwm.setPWM(ESC_CH, 0, v.toInt()); }
    }

  }

}

void turnRight() {
  Serial.println("Turning Right");
  pwm.setPWM(SERVO_CH, 0, 200);
}

void turnLeft() {
  Serial.println("Turning Left");
  pwm.setPWM(SERVO_CH, 0, 400);
}

void moveForward() {
  Serial.println("Moving Forward");
  pwm.setPWM(ESC_CH, 0, 315);
}

void moveBackward() {
  Serial.println("Moving Backward");
  pwm.setPWM(ESC_CH, 0, 285);
}

void stop() {
  Serial.println("Stopping");
  pwm.setPWM(ESC_CH, 0, 0);
}