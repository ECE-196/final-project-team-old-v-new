import asyncio
from bleak import BleakScanner, BleakClient
import struct
import numpy

CHARACTERISTIC_UUID_F = "19b10011-e8f2-537e-4f6c-d104768a1214"  
ACCELEROMETER_UUID_F = "19b10011-e8f2-537e-4f6c-d104768a1215"
CHARACTERISTIC_UUID_B = "19b10011-e8f2-537e-4f6c-d104768a1217"  
ACCELEROMETER_UUID_B = "19b10011-e8f2-537e-4f6c-d104768a1218"
DEVICE_NAME = ["SnowboardSensorFront","SnowboardSensorBack"]  

class BLEAdapter:
    def __init__(self):
        self.data_F = []
        self.data_B = []
        self.client_F = None
        self.client_B = None
        self.SERVICE_F = 0
        self.SERVICE_B = 0
        return

    async def send_data(self, client, val_F, val_B):
        await client.write_gatt_char(CHARACTERISTIC_UUID_F, bytearray([val_F]), response=True)
        await client.write_gatt_char(CHARACTERISTIC_UUID_B, bytearray([val_B]), response=True)

    async def read_data(self): 
        try:
            if(self.client_F):
                bytesRead_F = await self.client_F.read_gatt_char(ACCELEROMETER_UUID_F)
                val_F = struct.unpack('6f', bytesRead_F)
                self.data_F = val_F
            if(self.client_B):
                bytesRead_B = await self.client_B.read_gatt_char(ACCELEROMETER_UUID_B)
                val_B = struct.unpack('6f', bytesRead_B)
                self.data_B = val_B
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
        global SERVICE_F, SERVICE_B
        scanner = BleakScanner()
        print(f"Scanner Initialization Success")
        devices = await scanner.discover()
        print(f"Discovered Device List...")
        for device in devices:
            if device.name in DEVICE_NAME:
                print(f"Located target Device...")
                print("name: " + device.name)
                if (device.name == DEVICE_NAME[0]):
                    self.client_F = BleakClient(device, timeout=10)
                    await self.client_F.connect()
                    print(f"Connecting...")
                    print(f"Connected to device: {device.name}")
                    if(self.client_F.services):
                        self.SERVICE_F = 1
                else:
                    self.client_B = BleakClient(device, timeout=10)
                    await self.client_B.connect()
                    print(f"Connecting...")
                    print(f"Connected to device: {device.name}")
                    if(self.client_B.services):
                        self.SERVICE_B = 1      
        
                    #await read_data(client)
                if self.SERVICE_F == 1 and self.SERVICE_B == 1:
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
