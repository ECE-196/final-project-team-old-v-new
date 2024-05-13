#include <ArduinoBLE.h>
//#include <Adafruit_MPU6050.h>
//#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <stdio.h>

#define BaudRate 115200
#define NUMBYTESFROMACC 24
#define NUMVALUESFROMACC 6
#define SDApin  21    //IO 21 SDA
#define SCLpin  22    //IO 22 SCL
#define Acc_Sensitivity 16384.00 
const int buzzer = 1; //buzzer to arduino pin 1 GPIO1

BLEService sensorService("19b10010-e8f2-537e-4f6c-d104768a1220"); // create service

BLEByteCharacteristic switchCharacteristic("19b10011-e8f2-537e-4f6c-d104768a1217", BLERead | BLEWrite); // create characteristic
BLECharacteristic sendSensorChars("19b10011-e8f2-537e-4f6c-d104768a1218", BLERead | BLENotify, NUMBYTESFROMACC);
BLEByteCharacteristic calibrateCharacteristic("19b10011-e8f2-537e-4f6c-d104768a1219", BLERead | BLEWrite); // Tell measurements to calibrate

uint8_t MPU6050_WHO_AM_I = 0x75;
uint8_t MPU_ADDR = 0x68; // I2C address of the MPU-6050
size_t size = 24;
bool stopbit = false;
float accl_X, accl_Y, accl_Z, GyX, GyY, GyZ;
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
  BLE.setLocalName("SnowboardSensorBack");
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
      float sensorValues[NUMVALUESFROMACC] = { 
            // m/s^2
            accl_X,
            accl_Y, 
            accl_Z, 
            // Rotation - rad/s
            GyX,
            GyY, 
            GyZ
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
    tone(buzzer, 1000); // Send 1KHz sound signal...
    delay(500);        // ...for half sec
    noTone(buzzer);     // Stop sound...
    
  } else if(state == 2) {
    tone(buzzer, 1000); // Send 1KHz sound signal...
    delay(1000);        // ...for 1 sec
    noTone(buzzer);     // Stop sound...
  }
  else {
    //Serial.println("Buzzer off");
    noTone(buzzer);
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
  
  // Wait until all data is received
  if(Wire.available() == size) {
    // Read accelerometer data
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
  delay(50);
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
  Serial.print("| accl_X: ");
  Serial.print(accl_X);
  Serial.print(" g");
  Serial.print("\t");

  Serial.print("| accl_Y ");
  Serial.print(accl_Y);
  Serial.print(" g");
  Serial.print("\t");

  Serial.print("| accl_Z ");
  Serial.print(accl_Z);
  Serial.print(" g");
  Serial.print("\n");

  Serial.print("| GyX: ");
  Serial.print(GyX);
  Serial.print(" g");
  Serial.print("\t");

  Serial.print("| GyY ");
  Serial.print(GyY);
  Serial.print(" g");
  Serial.print("\t");

  Serial.print("| GyZ ");
  Serial.print(GyZ);
  Serial.print(" g");
  Serial.print("\n");

}