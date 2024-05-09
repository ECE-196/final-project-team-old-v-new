import asyncio
from bleak import BleakScanner, BleakClient
import struct
import numpy

CHARACTERISTIC_UUID = "19b10011-e8f2-537e-4f6c-d104768a1214"  # Replace with your characteristic UUID
ACCELEROMETER_UUID = "19b10011-e8f2-537e-4f6c-d104768a1215"
DEVICE_NAME = "SnowboardSensorFront"  # Replace with your device's name
SERVICE = 0

class BLEAdapter:
    def __init__(self):
        self.data = []
        self.client = None
        return

    async def send_data(self, client, value):
        await client.write_gatt_char(CHARACTERISTIC_UUID, bytearray([value]), response=True)

    async def read_data(self):
        try:
            bytesRead = await self.client.read_gatt_char(ACCELEROMETER_UUID)
            #print(bytesRead)
            value = struct.unpack('6f', bytesRead)
            self.data = value
            #print(self.data)
            return
        except Exception as error:
            print("An error occurred: ", error)
            return 0

        #print(f"Sensors read : {value}")

    async def cycle_data(self,client):
        print("Performing actions")
        for _ in range(5):  # Send data for about 20 seconds (5 cycles of 4 seconds each)
            await send_data(client, 1)  # Send value of 1
            await asyncio.sleep(2)  # Wait for 2 seconds
            await send_data(client, 0)  # Send value of 0
            await asyncio.sleep(2)  # Wait for 2 seconds
        
        await client.disconnect()

    async def scan_and_connect(self):
        scanner = BleakScanner()
        print(f"Scanner Initialization Success")
        devices = await scanner.discover()
        print(f"Discovered Device List...")
        for device in devices:
            if device.name == DEVICE_NAME:
                print(f"Located target Device...")
                self.client = BleakClient(device, timeout=10)
                await self.client.connect()
                print(f"Connecting...")
                print(f"Connected to device: {device.name}")
                if(self.client.services):
                    service = 1
                    #await read_data(client)
                return 1
            else:
                if (device.name):
                    print("name: " + device.name)
                else:
                    print(f"name: " + "unknown")
        print(f"ERROR: Connection Timeout")      
        print(f"Disabling Scanner...")   
        scanner.stop()
        print(f"Scanner Disabled...")  
        return 0

#asyncio.run(scan_and_connect())
