#include <ArduinoBLE.h>
//#include <Adafruit_MPU6050.h>
//#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <stdio.h>
#include <math.h>

#define BaudRate 115200
#define NUMBYTESFROMACC 24
#define NUMVALUESFROMACC 6
#define SDApin  21    //IO 21 SDA
#define SCLpin  22    //IO 22 SCL
#define Acc_Sensitivity 16384.00 
#define ALPHA 0.98
#define PI 3.14159265358979323846
const int buzzer = 1; //buzzer to arduino pin 1 GPIO1

BLEService sensorService("19b10010-e8f2-537e-4f6c-d104768a1212"); // create service

BLEByteCharacteristic switchCharacteristic("19b10011-e8f2-537e-4f6c-d104768a1214", BLERead | BLEWrite); // create characteristic
BLECharacteristic sendSensorChars("19b10011-e8f2-537e-4f6c-d104768a1215", BLERead | BLENotify, NUMBYTESFROMACC);
BLEByteCharacteristic calibrateCharacteristic("19b10011-e8f2-537e-4f6c-d104768a1216", BLERead | BLEWrite); // Tell measurements to calibrate

uint8_t MPU6050_WHO_AM_I = 0x75;
uint8_t MPU_ADDR = 0x68; // I2C address of the MPU-6050
size_t size = 24;
bool stopbit = false;
float accl_X, accl_Y, accl_Z, GyX, GyY, GyZ;
float accl_X_prev, accl_Y_prev, accl_Z_prev;
float pitch, yaw, roll;
float accl_X_offset = 0.0;
float accl_Y_offset = 0.0;
float accl_Z_offset = 0.0;
float GyX_offset = 0.0;
float GyY_offset = 0.0;
float GyZ_offset = 0.0;
float vx = 0;
float vy = 0;
float vz = 0;
unsigned long curr_time = 0;
 unsigned long prev_time = 0;
float dt = 0;
byte byteArray[NUMBYTESFROMACC];



void setup() {
  Serial.begin(115200);
   Wire.begin(SDApin, SCLpin, 100000); // sda, scl, clock speed
   Wire.beginTransmission(MPU_ADDR);
   Wire.write(0x6B);  // PWR_MGMT_1 register
   Wire.write(0);     // set to zero (wakes up the MPU−6050)
   Wire.endTransmission(true);
   WhoAmI();
   Serial.println("Setup complete");
  //pinMode(LED, OUTPUT);

  /*************** SETTING UP THE BLE MODE *******************/
  // begin initialization
  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }

  // set advertised local name and service UUID
  BLE.setLocalName("SnowboardSensorFront");
  BLE.setAdvertisedService(sensorService);
  BLE.setAdvertisingInterval(62);

  // TODO: REMOVE WHEN DONE
  sensorService.addCharacteristic(switchCharacteristic);

  // Main Characteristics
  sensorService.addCharacteristic(sendSensorChars);
  sensorService.addCharacteristic(calibrateCharacteristic);

  // add service
  BLE.addService(sensorService);
  // set the initial value for the characteristics
  switchCharacteristic.writeValue(0);
  calibrateCharacteristic.writeValue(0);

  byte sensorData[24] = {0x00}; 

  //sendSensorChars.writeValue(sensorData, sizeof(sensorData));

  // start advertising
  BLE.advertise();
  pinMode(buzzer, OUTPUT); // Set buzzer - pin 1 as an output

  calibrateAccel();
}

void loop() {
      
  
  BLEDevice central = BLE.central();
  if (central){
    while (central.connected()){
      // Detect when to activate buzzer
      if (switchCharacteristic.written()) {
        buzzerActivator(switchCharacteristic.value());
      }
      if(calibrateCharacteristic.written()) {
        performCalibration();
      }
      recordRegister();
      parseAccelOutput();
      float sensorValues[NUMVALUESFROMACC] = { 
            // m/s^2
            pitch,
            yaw, 
            roll, 
            // Rotation - rad/s
            vx,
            vy, 
            vz
      };
      for(int i = 0; i < NUMVALUESFROMACC; i++) {
          memcpy(&byteArray[i * sizeof(float)], &sensorValues[i], sizeof(float));
      }
      sendSensorChars.writeValue(byteArray,sizeof(byteArray));
    }
  }
  //printAccelValues();
  delay(50); 
}
/**
 * Activates the buzzers given a state from the interface.
*/
void buzzerActivator(int state) {
  if (state == 1) {
    //tone(buzzer, 1000); // Send 1KHz sound signal...
    digitalWrite(buzzer, HIGH);
    delay(5);        // ...for half sec
    //noTone(buzzer);     // Stop sound...
    digitalWrite(buzzer, LOW);
    
  } else if(state == 2) {
    //tone(buzzer, 1000); // Send 1KHz sound signal...
    digitalWrite(buzzer, HIGH);
    delay(1000);        // ...for 1 sec
    //noTone(buzzer);     // Stop sound...
    digitalWrite(buzzer, LOW);
  }
  else {
    //Serial.println("Buzzer off");
    //noTone(buzzer);
    digitalWrite(buzzer, LOW);
  }
  switchCharacteristic.writeValue(0); // Reset state
}

/**
 * Insert Calibration code here
*/
void performCalibration() {
  calibrateCharacteristic.writeValue(0); // Reset state
}

/**
 * Obtains accelerometer / gyroscope values from MPU6050 and stores it in global variables.
*/
void recordRegister() {
  Serial.println("Recording register...");
  Wire.beginTransmission(MPU_ADDR); // Start transmission to MPU
  Wire.write(0x3B); // Set register address to read accelerometer data
  Wire.endTransmission(); // End transmission
  
  Wire.requestFrom(MPU_ADDR, size, stopbit);
  //record previous accelerations
  accl_X_prev = accl_X;
  accl_Y_prev = accl_Y;
  accl_Z_prev = accl_Z;
  // Wait until all data is received
  if(Wire.available() == size) {
    // Read accelerometer data
    prev_time = curr_time;
    curr_time = millis()/1000.0;
    dt = curr_time - prev_time;
    accl_X = (Wire.read() << 8 | Wire.read())/Acc_Sensitivity; // Combine high and low bytes for X-axis
    accl_Y = (Wire.read() << 8 | Wire.read())/Acc_Sensitivity;; // Combine high and low bytes for Y-axis
    accl_Z = (Wire.read() << 8 | Wire.read())/Acc_Sensitivity;; // Combine high and low bytes for Z-axis
    GyX = (Wire.read() << 8 | Wire.read()) / 16384.0; // X-axis value
    GyY = (Wire.read() << 8 | Wire.read()) / 16384.0; // Y-axis value
    GyZ = (Wire.read() << 8 | Wire.read()) / 16384.0; // Z-axis value
    Serial.println("Data received successfully.");
  } else {
    Serial.println("Error: Data not available.");
  }
}

void WhoAmI(){
  uint8_t waiByte;                                    // Data will go here
  MPU6050_Read(MPU6050_WHO_AM_I, &waiByte);           // Get data
  Serial.print(F("Device WhoAmI reports as: 0x"));    // 
  Serial.println(waiByte,HEX);                        // Report WhoAmI data
  }

void MPU6050_Read(int address,uint8_t *data){            // Read from MPU6050. Needs register address, data array
  size_t sz = sizeof(*data);                              //
  Wire.beginTransmission(MPU_ADDR);           // Begin talking to MPU6050
  Wire.write(address);                                   // Set register address
  Wire.endTransmission(false);                           // Hold the I2C-bus
  Wire.requestFrom(MPU_ADDR, sz, true);     // Request bytes, release I2C-bus after data read
  int i = 0;                                             //
  while(Wire.available()){                               //
    data[i++]=Wire.read();                               // Add data to array
  }
}


void printAccelValues() {
  Serial.print("| pitch: ");
  Serial.print(pitch);
  Serial.print(" g");
  Serial.print("\t");

  Serial.print("| yaw ");
  Serial.print(yaw);
  Serial.print(" g");
  Serial.print("\t");

  Serial.print("| roll ");
  Serial.print(roll);
  Serial.print(" g");
  Serial.print("\n");

  Serial.print("| vx: ");
  Serial.print(vx);
  Serial.print(" g");
  Serial.print("\t");

  Serial.print("| vy ");
  Serial.print(vy);
  Serial.print(" g");
  Serial.print("\t");

  Serial.print("| vz ");
  Serial.print(vz);
  Serial.print(" g");
  Serial.print("\n");

}

void parseAccelOutput(){
  accl_X -= accl_X_offset;
  accl_Y -= accl_Y_offset;
  accl_Z -= accl_Z_offset;
  GyX -= GyX_offset;
  GyY -= GyY_offset;
  GyZ -= GyZ_offset;
  float pitch_acc  = (atan2(accl_Y, sqrt(pow(accl_X, 2) + pow(accl_Z, 2))))*180/PI;
  float roll_acc = atan2(-accl_X, accl_Z)*180/PI;
  pitch = ALPHA * (pitch + GyX * dt) + (1 - ALPHA) * pitch_acc;
  roll = ALPHA * (roll + GyY * dt) + (1 - ALPHA) * roll_acc;
  yaw = yaw + GyZ * dt;
  vx += (accl_X_prev + accl_X) * dt / 2.0;
  vy += (accl_Y_prev + accl_Y) * dt / 2.0;
  vz += (accl_Z_prev + accl_Z) * dt / 2.0;

}

void calibrateAccel(){
  int i = 1000;
  while (i > 0){
    recordRegister();
    accl_X_offset += accl_X;
    accl_Y_offset += accl_Y;
    accl_Z_offset += accl_Z;
    GyX_offset += GyX;
    GyY_offset += GyY;
    GyZ_offset += GyZ;
    i--;
    delay(10);
  }
  accl_X_offset /= 1000;
  accl_Y_offset /= 1000;
  accl_Z_offset /= 1000;
  GyX_offset/= 1000;
  GyY_offset/= 1000;
  GyZ_offset/= 1000;
}

