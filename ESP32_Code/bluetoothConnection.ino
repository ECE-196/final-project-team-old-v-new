#include <ArduinoBLE.h>

BLEService ledService("19b10010-e8f2-537e-4f6c-d104768a1214"); // create service

BLEByteCharacteristic switchCharacteristic("19b10011-e8f2-537e-4f6c-d104768a1214", BLERead | BLEWrite); // create characteristic
BLECharacteristic sendAccChars("19b10011-e8f2-537e-4f6c-d104768a1215", BLERead | BLENotify, 8);

const int LED{17};

void setup() {
  Serial.println("Starting!");
  Serial.begin(9600);
  while (!Serial);

  pinMode(LED, OUTPUT);

  // begin initialization
  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }

  Serial.println("Starting part 2!");
  // set advertised local name and service UUID
  BLE.setLocalName("Aether's LED");
  BLE.setAdvertisedService(ledService);

  Serial.println("Adding characteristic to service!");
  // add the characteristic to the service
  ledService.addCharacteristic(switchCharacteristic);
  ledService.addCharacteristic(sendAccChars);

  Serial.println("Adding service!");
  // add service
  BLE.addService(ledService);

  Serial.println("Setting initial value for the characteristic!");
  // set the initial value for the characteristic
  switchCharacteristic.writeValue(0);

  byte sensorData[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}; 

  sendAccChars.writeValue(sensorData, sizeof(sensorData));

  // start advertising
  BLE.advertise();

  Serial.println("BLE LED Peripheral");
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
      byte sensorData[] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07}; 
      sendAccChars.writeValue(sensorData, sizeof(sensorData));

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