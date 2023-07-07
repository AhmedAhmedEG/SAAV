#include <Adafruit_PWMServoDriver.h>
#include "Adafruit_VL53L0X.h"
#include <NewPing.h>

#define SERVO_FREQ 50
#define SERVO_CH 15
#define ESC_CH 11
#define TOF1_ADDRESS 0x30
#define TOF1_SHUT D5
#define TOF2_ADDRESS 0x31
#define TOF2_SHUT D4
#define trig_pin0 D6
#define echo_pin0 D0
#define trig_pin1 D8
#define echo_pin1 D7
#define MAX_DISTANCE 200

bool avoid = false;
int last_speed = 320;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

NewPing sonar[2] = {
NewPing(trig_pin0, echo_pin0, MAX_DISTANCE),
NewPing(trig_pin1, echo_pin1, MAX_DISTANCE),
};

Adafruit_VL53L0X tof1 = Adafruit_VL53L0X();
Adafruit_VL53L0X tof2 = Adafruit_VL53L0X();

VL53L0X_RangingMeasurementData_t tof1_measure;
VL53L0X_RangingMeasurementData_t tof2_measure;

void turn(int a) {
  int v = map(a, 0, 180, 180, 455);
  pwm.setPWM(SERVO_CH, 0, v);
}

void move(int s) {
  pwm.setPWM(ESC_CH, 0, s);
}

class Avoider {

  private:
    int previousTime = millis();
    int reactionTime = 0;
    int waitReactionTime = 2000;
    int reactionDistance = 40;
    char currentDirection = 'f';

  public:

    void check() {

      int timePassed = millis() - previousTime;
      if (timePassed >= reactionTime) {
        previousTime = millis();

        int readings[4];

        tof1.rangingTest(&tof1_measure, false);
        if(tof1_measure.RangeStatus != 4) {
          readings[0] = tof1_measure.RangeMilliMeter / 10;
        } else {
          readings[0] = 8191;
        }

        tof2.rangingTest(&tof2_measure, false);
        if(tof2_measure.RangeStatus != 4) {
          readings[1] = tof2_measure.RangeMilliMeter / 10;
        } else {
          readings[1] = 8191;
        }

        for (int i = 2; i < 4; i++) {
          int us = sonar[i - 2].ping_median();
          readings[i] = sonar[i - 2].convert_cm(us);

          if (readings[i] == 0) {readings[i] = 200;}

        }

        Serial.print("Left: ");
        Serial.print(readings[0]);
        Serial.print(", Right: ");
        Serial.print(readings[1]);
        Serial.print(", Middle: ");
        Serial.print(readings[2]);
        Serial.print(", Back: ");
        Serial.println(readings[3]);

        if (readings[2] > reactionDistance) {turn(90); move(last_speed); return;}

        move(0);
        delay(250);

        if ((readings[0] >= readings[1]) && (readings[0] > reactionDistance)) {turn(0); currentDirection = 'r'; move(last_speed);}
        else if ((readings[1] >= readings[0]) && (readings[1] > reactionDistance)) {turn(180); currentDirection = 'l'; move(last_speed);}
        else {turn(90); move(0); return;}

        wait();
      }

    }

    void wait() {

      while (true) {
        int timePassed = millis() - previousTime;

        if (timePassed >= waitReactionTime) {

          int readings[4];

          tof1.rangingTest(&tof1_measure, false);
          if(tof1_measure.RangeStatus != 4) {
            readings[0] = tof1_measure.RangeMilliMeter / 10;
          } else {
            readings[0] = 8191;
          }

          tof2.rangingTest(&tof2_measure, false);
          if(tof2_measure.RangeStatus != 4) {
            readings[1] = tof2_measure.RangeMilliMeter / 10;
          } else {
            readings[1] = 8191;
          }

          for (int i = 2; i < 4; i++) {
            int us = sonar[i - 2].ping_median();
            readings[i] = sonar[i - 2].convert_cm(us);

            if (readings[i] == 0) {readings[i] = 200;}

          }

          Serial.print("Left: ");
          Serial.print(readings[0]);
          Serial.print(", Right: ");
          Serial.print(readings[1]);
          Serial.print(", Middle: ");
          Serial.print(readings[2]);
          Serial.print(", Back: ");
          Serial.println(readings[3]);
          
          if ((currentDirection == 'r') && (readings[0] < reactionDistance)) {move(0); delay(1000);}
          else if ((currentDirection == 'r') && (readings[0] > reactionDistance)) {move(last_speed);}
          else if ((currentDirection == 'l') && (readings[1] < reactionDistance)) {move(0); delay(1000);}
          else if ((currentDirection == 'l') && (readings[1] > reactionDistance)) {move(last_speed);}

          if (readings[2] > reactionDistance) {turn(90); move(last_speed); break;}

        }

      }

    }

};

Avoider avoider;

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(1); }
  
  pwm.begin();
  pwm.setPWMFreq(SERVO_FREQ);

  pinMode(TOF1_SHUT, OUTPUT);
  pinMode(TOF2_SHUT, OUTPUT);

  digitalWrite(TOF1_SHUT, LOW);
  digitalWrite(TOF2_SHUT, LOW);

  setupTofs();

  move(300);
  delay(1000);
}

void loop() {
  avoider.check();
}

void setupTofs() {
  // all reset
  digitalWrite(TOF1_SHUT, LOW);    
  digitalWrite(TOF2_SHUT, LOW);
  delay(10);
  // all unreset
  digitalWrite(TOF1_SHUT, HIGH);
  digitalWrite(TOF2_SHUT, HIGH);
  delay(10);

  // activating LOX1 and resetting LOX2
  digitalWrite(TOF1_SHUT, HIGH);
  digitalWrite(TOF2_SHUT, LOW);

  // initing LOX1
  if(!tof1.begin(TOF1_ADDRESS)) {
    Serial.println(F("Failed to boot first VL53L0X"));
    while(1);
  }
  delay(10);

  // activating LOX2
  digitalWrite(TOF2_SHUT, HIGH);
  delay(10);

  //initing LOX2
  if(!tof2.begin(TOF2_ADDRESS)) {
    Serial.println(F("Failed to boot second VL53L0X"));
    while(1);
  }
}