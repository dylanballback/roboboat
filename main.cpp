#include <Arduino.h>
#include <CrsfSerial.h>  // https://github.com/CapnBry/CRServoF/
#include "calibration.h"
#include <Servo.h>
#include <cmath>

//Sin wave PCB Testing Stuff.
double sineWaveFrequency = 0.01; //Hz
unsigned long previousTime = 0;
unsigned long startTime = 0;


// BOARD_ID SELECTION HAPPENS IN PLATFORMIO ENVIRONMENT SELECTION

// Blink routine variables and state tracking
#define BLINK_ENABLED                    // comment this line out to disable led blink
#define BLINK_TIME 60000                 // blink routine window (in ms)
#define BLINK_DELAY 500                  // delay in between led state change (in ms)

static bool serialEcho;
static char serialInBuff[64];
static uint8_t serialInBuffLen;

bool led_state = false;                  // track led on/off state
unsigned long ms_curr = 0;               // current time
unsigned long ms_last_link_changed = 0;  // last time crsf link changed
unsigned long ms_last_led_changed = 0;   // last time led changed state in blink routine

#include "board_defs.h"


//----------------Boat Setup START------------------------------
Servo frontServo;
Servo backServo;
Servo frontMotorESC;
Servo backMotorESC;

// Front Motor/Servo Pins  (Autonomous boat V0.1 2/3/24 PCB)
#define FRONT_MOTOR_PIN 16 // Front Motor ESC connected to GP16 3.3v
#define FRONT_SERVO_PIN 17 // Front Servo connected to GP17 3.3v

// Back Motor/Servo Pins 
#define BACK_MOTOR_PIN 18  // Back Motor ESC connected to GP18 3.3v
#define BACK_SERVO_PIN 19  // Back Servo connected to GP19 3.3v


#define ESTOP_PIN 13 // E-Stop relay pin connected to GP13

#define AUTONOMOUS_PIN 11 // Autonomous/RC relays connected to PG11

//Water Cannon
#define WATER_CANNON_SERVO_1 9 // Servo 1 connected to GP9
#define WATER_CANNON_SERVO_2 8 // Servo 2 connected to GP8

#define WATER_CANNON_RELAY 6 // Water Cannon Relay connected to GP6


//Motor Offset 
int frontMotorOffset = 10;

int backMotorOffset = -10;


//Motor thrust idle value (May need fine tuning)
int idleThrust = 0; 
int noThrust = 0;

//Servo Direction (May need fine tuning)
int leftFront = 40;
int leftBack = 35;

int straightFront = 100;
int straightBack = 95;


int rightFront = 160;
int rightBack = 155;

bool isCalibrated = false; // Global variable to track calibration status


void calibrateMotors() {
    // First, set to full throttle forward (1900 us Full Forward Throttle)
    frontMotorESC.writeMicroseconds(1500); // Full throttle forward for calibration start
    backMotorESC.writeMicroseconds(1500);

    delay(2000); // Delay for 2 seconds to ensure the ESCs register the max throttle signal
}

//----------------Boat Setup


//----------------Boat Setup END--------------------------------



UART Serial2(CRSF_TX, CRSF_RX, NC, NC);

CrsfSerial crsf(Serial2, CRSF_BAUDRATE); // pass any HardwareSerial port




//----------------Drift Cart FUNCTIONS START------------------------------

// Define varibale to store channel data 
uint16_t channels[8];

void printChannelData() {
    for (int i = 0; i < 8; i++) {
        Serial.print("Channel ");
        Serial.print(i + 1);
        Serial.print(": ");
        Serial.println(channels[i]);
    }
    Serial.println();
    Serial.println();
    Serial.println();
    Serial.println();
}

void sinwave() {


}


//Get channel data 
// Will loop through and get 9 channel data
// Then send it to the printChannelData fucntion 

void packetChannels() {
    for (int i = 0; i < 8; i++) {
        channels[i] = crsf.getChannel(i + 1);
    }
    //printChannelData();

    // Update servo positions
    int frontServoPosition = map(channels[0], 999, 2000, 0, 180); // Example for channel 1
    int backServoPosition = map(channels[1], 999, 2000, 0, 180); // Example for channel 2

    // Update motor speeds
    //Throttle limited to 1300 for reverse and 1700 forward
    // 1100 is max reverse
    // 1900 is max forward 
    // We are running at 24V so we need to limit power to not burn out motors.
    int motorSpeed = map(channels[2], 1000, 2000, 1200, 1800); // Example for channel 3

    // Check if motorSpeed is within the specified range
    if (motorSpeed >= 1475 && motorSpeed <= 1525) {
        motorSpeed = 1500; // Set motorSpeed to 1500 if it's within the range
    }

    //RC SF Switch channel data for triggering E-Stop; Down is E-Stop ON (Power OFF); Up is E-Stop OFF (Power ON)
    int EStop = channels[4];

    // Print the EStop Channel Data for Testing:
    //Serial.print("E-Stop Switch:  ");
    //Serial.println(channels[4]);
    //Serial.println();

    //For Autonomous / RC Control Relays Switch
    int autonomousRCswitch = channels[5]; //Get channel data from RC Swtich SB
    int autonomousState = 0; 

    // Print the Autonomous / RC Control Relays Switch Channel Data for Testing:
    //Serial.print("RC/Auto Switch: ");
    //Serial.println(channels[5]);
    //Serial.println();

    if (autonomousRCswitch == 2000){ //RC SB Swtich BACK Position
       autonomousState = 1; 
       digitalWrite(AUTONOMOUS_PIN, LOW); //Turn Autonomous Relays to ON 
    } 
    else if (autonomousRCswitch == 1500) { //RC SB Swtich Middle Position
      autonomousState = 0; 
      digitalWrite(AUTONOMOUS_PIN, HIGH); //Turn Autonomous Relays to Off on Startup
    } 
    else if (autonomousRCswitch == 1000) { //RC SB Swtich FRONT Position
      autonomousState = 0; 
      digitalWrite(AUTONOMOUS_PIN, HIGH); //Turn Autonomous Relays to OFF on Startup
    }
    //Serial.print("Linear Actuator State: ");
    //Serial.println(autonomousState);


    //Serial.print("Front Servo Position: ");
    //Serial.println(frontServoPosition);
    //Serial.print("Back Servo Position: ");
    //Serial.println(backServoPosition);
    //Serial.print("Motor Speed: ");
    //Serial.println(motorSpeed);

    //Serial.print("E-Stop Status: ");
    //Serial.println(EStop);

    // EStop Pin HIGH = E-Stop ON (No Power to motors)
    // EStop Pin LOW  = E-Stop OFF (Power to Motors)
    if (EStop == 1000) {
      digitalWrite(ESTOP_PIN, HIGH);
      isCalibrated = false; // Reset calibration flag
      digitalWrite(LED_BUILTIN, HIGH); //Turn ON Onboard Pico LED when E-Stop is off
    } else if (EStop == 2000 && !isCalibrated) {
      digitalWrite(ESTOP_PIN, LOW);
      delay(2000); //Delay 2 Seconds.
      calibrateMotors(); //Initalize Motors after E-Stop is turned of (power is on)
      isCalibrated = true; // Set flag to prevent re-calibration
      digitalWrite(LED_BUILTIN, LOW); // Turn on onboard pico LED when E-Stop is on
    }

    //RC SC Switch channel data for triggering Water Cannon Relay; Down is Water Cannon ON (Power ON); Up is Water Cannon OFF (Power OFF)
    int WaterCannonRelay = channels[6];

    if (WaterCannonRelay == 1000) {
      digitalWrite(WATER_CANNON_RELAY, HIGH);
    } else if (WaterCannonRelay == 2000) {
      digitalWrite(WATER_CANNON_RELAY, LOW);
    }

// Code to make RC Controls drive like our basic autonomous software controls
    //int rightStickHORIZONTAL = channels[0];

    //if (rightStickHORIZONTAL <= 1100) {
        //Turn Left
    //    frontServo.write(leftFront); //Turn both servos left
    //    backServo.write(leftBack);
    //}
    //else if (rightStickHORIZONTAL >= 1400 && rightStickHORIZONTAL <= 1600) {
        //Striaght
    //    frontServo.write(straightFront); //Turn both servos straight
    //    backServo.write(straightBack);
    //} else if (rightStickHORIZONTAL >= 1800) {
        //Turn Right
    //    frontServo.write(rightFront); //Turn both servos to the right
    //    backServo.write(rightBack);
    //}

// Not needed becuase we want out boat to drive like the autonomous simple code above.
    frontServo.write(frontServoPosition);
    backServo.write(frontServoPosition+10);
    //frontMotorESC.writeMicroseconds(motorSpeed);
    //backMotorESC.writeMicroseconds(motorSpeed);
}


//----------------Boat FUNCTIONS END------------------------------


void crsfLinkUp() {
  ms_last_link_changed = millis();
  ms_last_led_changed = ms_last_link_changed;
  led_state = true;
  led_on();
}

void crsfLinkDown() {
  ms_last_link_changed = millis();
  ms_last_led_changed = ms_last_link_changed;
  led_state = false;
  led_off();
}

static void passthroughBegin(uint32_t baud)
{
    if (baud != crsf.getBaud())
    {
        // Force a reboot command since we want to send the reboot
        // at 420000 then switch to what the user wanted
        const uint8_t rebootpayload[] = { 'b', 'l' };
        crsf.queuePacket(CRSF_ADDRESS_CRSF_RECEIVER, CRSF_FRAMETYPE_COMMAND, &rebootpayload, sizeof(rebootpayload));
    }
    crsf.setPassthroughMode(true, baud);
    
    serialEcho = false;
}

static void crsfOobData(uint8_t b)
{
    Serial.write(b);
}

/***
 * @brief Processes a text command like we're some sort of CLI or something
 * @return true if CrsfSerial was placed into passthrough mode, false otherwise
*/
static bool handleSerialCommand(char *cmd)
{
    // Fake a CRSF RX on UART6
    bool prompt = true;
    if (strcmp(cmd, "#") == 0)
    {
        Serial.println("Fake CLI Mode, type 'exit' or 'help' to do nothing\r\n");
        serialEcho = true;
    }

    else if (strcmp(cmd, "serial") == 0)
        Serial.println("serial 5 64 0 0 0 0\r\n");

    else if (strcmp(cmd, "get serialrx_provider") == 0)
        Serial.println("serialrx_provider = CRSF\r\n");

    else if (strcmp(cmd, "get serialrx_inverted") == 0)
        Serial.println("serialrx_inverted = OFF\r\n");

    else if (strcmp(cmd, "get serialrx_halfduplex") == 0)
        Serial.println("serialrx_halfduplex = OFF\r\n");

    else if (strncmp(cmd, "serialpassthrough 5 ", 20) == 0)
    {
        Serial.println(cmd);

        unsigned int baud = atoi(&cmd[20]);
        passthroughBegin(baud);

        return true;
    }

    else
        prompt = false;

    if (prompt)
        Serial.print("# ");

    return false;
}

static void checkSerialInNormal()
{
    while (Serial.available())
    {
        char c = Serial.read();
        if (serialEcho && c != '\n')
            Serial.write(c);

        if (c == '\r' || c == '\n')
        {
            if (serialInBuffLen != 0)
            {
                Serial.write('\n');
                serialInBuff[serialInBuffLen] = '\0';
                serialInBuffLen = 0;

                bool goToPassthrough = handleSerialCommand(serialInBuff);
                // If need to go to passthrough, get outta here before we dequeue any bytes
                if (goToPassthrough)
                    return;
            }
        }
        else
        {
            serialInBuff[serialInBuffLen++] = c;
            // if the buffer fills without getting a newline, just reset
            if (serialInBuffLen >= sizeof(serialInBuff))
                serialInBuffLen = 0;
        }
    }  /* while Serial */
}

static void checkSerialInPassthrough()
{
    static uint32_t lastData = 0;
    static bool LED = false;
    bool gotData = false;
    unsigned int avail;
    while ((avail = Serial.available()) != 0)
    {
        uint8_t buf[16];
        avail = Serial.readBytes((char *)buf, min(sizeof(buf), avail));
        crsf.write(buf, avail);
        LED ? led_on() : led_off();
        LED = !LED;
        gotData = true;
    }
    // If longer than X seconds since last data, switch out of passthrough
    if (gotData || !lastData)
        lastData = millis();

    // Turn off LED 1s after last data
    else if (LED && (millis() - lastData > 1000))
    {
        LED = false;
        led_off();
    }

    // Short blink LED after timeout
    else if (millis() - lastData > 5000)
    {
        lastData = 0;
        led_on();
        delay(200);
        led_off();
        crsf.setPassthroughMode(false);
    }
}

static void checkSerialIn()
{
    if (crsf.getPassthroughMode())
        checkSerialInPassthrough();
    else
        checkSerialInNormal();
}

#ifdef BLINK_ENABLED
void led_loop() {
  ms_curr = millis();
  // link is down
  if(!crsf.isLinkUp()) {
    // within the blink routine window (BLINK_TIME)
    if(ms_curr < (ms_last_link_changed + BLINK_TIME)) {
      // handle led toggle delay
      if(ms_curr > (ms_last_led_changed + BLINK_DELAY)) {
        ms_last_led_changed = ms_curr;
        led_state ? led_on() : led_off();
        led_state = !led_state;  // toggle led state
      }
    }
    else
    {
      // ensure the led is off if the blink routine expired and link is down
      led_off();
    }
  }
}
#endif

void setup()
{
    Serial.begin(115200);
    boardSetup();
    crsfLinkDown();

    // Attach the channels callback
    crsf.onPacketChannels = &packetChannels;
    crsf.onLinkUp = &crsfLinkUp;
    crsf.onLinkDown = &crsfLinkDown;
    crsf.onOobData = &crsfOobData;
    crsf.begin();
    serialEcho = true;

    // Set the minimum pulse width to 500 microseconds
    // Set the maximum pulse width to 2500 microseconds
    frontServo.attach(FRONT_SERVO_PIN, 500, 2500);
    backServo.attach(BACK_SERVO_PIN, 500, 2500);

    //Blue T200 ESC 
    //Initialize/Stop == 1500 us
    //Full Throttle Forward == 1900 us 
    //Full Throttle Reverse == 1100 us

    frontMotorESC.attach(FRONT_MOTOR_PIN, 1100, 1900);
    backMotorESC.attach(BACK_MOTOR_PIN, 1100, 1900);

    //Set up E-Stop and Autonomous/RC signals as output.
    pinMode(ESTOP_PIN, OUTPUT);
    pinMode(AUTONOMOUS_PIN, OUTPUT);

    digitalWrite(ESTOP_PIN, HIGH); //Turn on E-Stop on Startup

    digitalWrite(AUTONOMOUS_PIN, LOW); //Turn Autonomous Relays to Off on Startup

    startTime = millis();
    Serial.print("Setup Complete");

}

void loop()
{
    // Must call CrsfSerial.loop() in loop() to process data
    crsf.loop();
    checkSerialIn();
    #ifdef BLINK_ENABLED
    led_loop();
    #endif
    
    unsigned long currentTime = millis();
    
    if (currentTime - startTime > 60000) { //60 second delay
        // Generate sine wave for motor control
        unsigned long currentTime = millis();
        if (currentTime - previousTime >= 100) {  // Update every 100 milliseconds
            previousTime = currentTime;

            double timeInSeconds = currentTime / 1000.0;
            double sineWaveValue = sin(2 * PI * sineWaveFrequency * timeInSeconds);

            // Map the sine wave value (-1 to 1) to motor speed range (1100 to 1900)
            int motorSpeed = map(sineWaveValue * 100, -100, 100, 1500, 1900);

            Serial.println(motorSpeed);
            // Apply the sine wave value to motor speeds
            frontMotorESC.writeMicroseconds(motorSpeed);
            backMotorESC.writeMicroseconds(motorSpeed);
        }
    }
}
