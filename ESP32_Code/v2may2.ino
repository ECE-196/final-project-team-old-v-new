#include <ArduinoBLE.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

#define NUMBYTESFROMACC 24
#define NUMVALUESFROMACC 6

BLEService sensorService("19b10010-e8f2-537e-4f6c-d104768a1214"); // create service

BLEByteCharacteristic switchCharacteristic("19b10011-e8f2-537e-4f6c-d104768a1214", BLERead | BLEWrite); // create characteristic
BLECharacteristic sendSensorChars("19b10011-e8f2-537e-4f6c-d104768a1215", BLERead | BLENotify, NUMBYTESFROMACC);
BLEByteCharacteristic calibrateCharacteristic("19b10011-e8f2-537e-4f6c-d104768a1216", BLERead | BLEWrite); // Tell measurements to calibrate

Adafruit_MPU6050 mpu;

const int LED{17};

struct accel{
  int offsetX{0};
  int offsetY{0};
  int offsetZ{0};  
};
struct angularV{
  int offsetX{0};
  int offsetY{0};
  int offsetZ{0};  
};

float testingValues[NUMVALUESFROMACC] = { 8.88, 9.99, 10.10, 6.66, 4.20, 21.21};
byte byteArray[NUMBYTESFROMACC];

void setup() {
  Serial.begin(9600);
  while (!Serial);

  pinMode(LED, OUTPUT);

  /*************** SETTING UP THE BLE MODE *******************/
  // begin initialization
  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }

  // set advertised local name and service UUID
  BLE.setLocalName("SnowboardSensorFront");
  BLE.setAdvertisedService(sensorService);

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

  sendSensorChars.writeValue(sensorData, sizeof(sensorData));

  // start advertising
  BLE.advertise();

  /*************** SETTING UP THE ACCELEROMETER SENSORS *******************/
  Serial.println("Adafruit MPU6050 test!");

  // Try to initialize!
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  Serial.print("Accelerometer range set to: ");
  switch (mpu.getAccelerometerRange()) {
  case MPU6050_RANGE_2_G:
    Serial.println("+-2G");
    break;
  case MPU6050_RANGE_4_G:
    Serial.println("+-4G");
    break;
  case MPU6050_RANGE_8_G:
    Serial.println("+-8G");
    break;
  case MPU6050_RANGE_16_G:
    Serial.println("+-16G");
    break;
  }
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.print("Gyro range set to: ");
  switch (mpu.getGyroRange()) {
  case MPU6050_RANGE_250_DEG:
    Serial.println("+- 250 deg/s");
    break;
  case MPU6050_RANGE_500_DEG:
    Serial.println("+- 500 deg/s");
    break;
  case MPU6050_RANGE_1000_DEG:
    Serial.println("+- 1000 deg/s");
    break;
  case MPU6050_RANGE_2000_DEG:
    Serial.println("+- 2000 deg/s");
    break;
  }

  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);
  Serial.print("Filter bandwidth set to: ");
  switch (mpu.getFilterBandwidth()) {
  case MPU6050_BAND_260_HZ:
    Serial.println("260 Hz");
    break;
  case MPU6050_BAND_184_HZ:
    Serial.println("184 Hz");
    break;
  case MPU6050_BAND_94_HZ:
    Serial.println("94 Hz");
    break;
  case MPU6050_BAND_44_HZ:
    Serial.println("44 Hz");
    break;
  case MPU6050_BAND_21_HZ:
    Serial.println("21 Hz");
    break;
  case MPU6050_BAND_10_HZ:
    Serial.println("10 Hz");
    break;
  case MPU6050_BAND_5_HZ:
    Serial.println("5 Hz");
    break;
  }
}

void loop() {
  // listen for BLE peripherals to connect:
  BLEDevice central = BLE.central();

  // if a central is connected to peripheral:
  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    // while the central is still connected to peripheral:
    while (central.connected()) {
      /* Get new sensor events with the readings */
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);

      // accelerometer/gyroscope readings 
      // (accounting for their offset)
      float sensorValues[NUMVALUESFROMACC] = { 
        // m/s^2
        a.acceleration.x - accel.offsetX,
        a.acceleration.y - accel.offsetY, 
        a.acceleration.z - accel.offsetZ, 
        // Rotation - rad/s
        g.gyro.x - angularV.offsetX, 
        g.gyro.y - angularV.offsetY, 
        g.gyro.z - angularV.offsetZ
      };

      // Convert the float array to a byte array
      for(int i = 0; i < NUMVALUESFROMACC; i++) {
        memcpy(&byteArray[i * sizeof(float)], &testingValues[i], sizeof(float));
      }
      
      sendSensorChars.writeValue(byteArray,sizeof(byteArray));
      //sendSensorChars.writeValue(sensorData, sizeof(sensorData));

      // TODO : REMOVE WHEN DONE
      if (switchCharacteristic.written()) {
        if (switchCharacteristic.value()) {
          Serial.println("LED on");
          digitalWrite(LED, HIGH);
          
        } else {
          Serial.println("LED off");
          digitalWrite(LED, LOW);
        }
      }
      if (calibrateCharacteristic.written()) {
        if (calibrateCharacteristic.value()) {
          accel.offsetX = a.acceleration.x;
          accel.offsetY = a.acceleration.y;
          accel.offsetZ = a.acceleration.z;
          angularV.offsetX = g.acceleration.x;
          angularV.offsetY = g.acceleration.y;
          angularV.offsetZ = g.acceleration.z;
          calibrateCharacteristic.writeValue(2); // Calibration Done Flag is 0x02
        } else {
          // Do nothing
        }
      }
      delay(500); 
    }

    // central disconnected
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}