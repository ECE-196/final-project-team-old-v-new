#include <ArduinoBLE.h>

#define NUMBYTESFROMACC 24

BLEService sensorService("19b10010-e8f2-537e-4f6c-d104768a1214"); // create service

BLEByteCharacteristic switchCharacteristic("19b10011-e8f2-537e-4f6c-d104768a1214", BLERead | BLEWrite); // create characteristic
BLECharacteristic sendSensorChars("19b10011-e8f2-537e-4f6c-d104768a1215", BLERead | BLENotify, NUMBYTESFROMACC);
BLEByteCharacteristic calibrateCharacteristic("19b10011-e8f2-537e-4f6c-d104768a1216", BLERead | BLEWrite); // Tell measurements to calibrate

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

float testingValues[6] = { 8.88, 9.99, 10.10, 6.66, 4.20, 21.21};
byte byteArray[NUMBYTESFROMACC];

void setup() {
  Serial.begin(9600);
  while (!Serial);

  pinMode(LED, OUTPUT);

  // begin initialization
  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }

  // set advertised local name and service UUID
  BLE.setLocalName("Aether's LED");
  BLE.setAdvertisedService(sensorService);

  // TODO: REMOVE WHEN DONE
  sensorService.addCharacteristic(switchCharacteristic);

  // Main Characteristics
  sensorService.addCharacteristic(sendSensorChars);
  sensorService.addCharacteristic(calibrateCharacteristic);

  // add service
  BLE.addService(sensorService);
  // set the initial value for the characteristic
  switchCharacteristic.writeValue(0);

  byte sensorData[24] = {0x00}; 

  sendSensorChars.writeValue(sensorData, sizeof(sensorData));

  // start advertising
  BLE.advertise();
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
      // if the remote device wrote to the characteristic,
      // use the value to control the LED:
      // float testingValues[6] = { 8.88, 9.99, 10.10, 6.66, 4.20, 21.21};

      // Convert the float array to a byte array
      for(int i = 0; i < 6; i++) {
        memcpy(&byteArray[i * sizeof(float)], &testingValues[i], sizeof(float));
      }
      
      sendSensorChars.writeValue(byteArray,sizeof(byteArray));
      //sendSensorChars.writeValue(sensorData, sizeof(sensorData));

      if (switchCharacteristic.written()) {
        if (switchCharacteristic.value()) {
          Serial.println("LED on");
          digitalWrite(LED, HIGH);
          
        } else {
          Serial.println("LED off");
          digitalWrite(LED, LOW);
        }
      }
    }

    // central disconnected
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}