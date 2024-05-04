from __future__ import annotations
from typing import Optional
from serial import Serial, SerialException
from serial.tools.list_ports import comports
#########################################################################################
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import showerror
from threading import Thread, Lock # we'll use Lock later ;)

def detached_callback(f):
    return lambda *args, **kwargs: Thread(target=f, args=args, kwargs=kwargs).start()

S_OK: int = 0xaa
S_ERR: int = 0xff

import asyncio
from bleak import BleakScanner, BleakClient

CHARACTERISTIC_UUID = "19b10011-e8f2-537e-4f6c-d104768a1214"  # Replace with your characteristic UUID
DEVICE_NAME = "Aether's LED"  # Replace with your device's name
toggler = 0

async def send_data(client, value):
    await client.write_gatt_char(CHARACTERISTIC_UUID, bytearray([value]), response=True)

async def scan():
    global devices  # Declare devices as a global variable
    global device
    scanner = BleakScanner()
    devices = await scanner.discover()
    device = devices[0]

async def connectBLE(device):
    async with BleakClient(device) as client:
        print(f"Connected to device: {device.name}")
        await cycle_data(client)

async def cycle_data(client):
    print("Performing actions")
    for _ in range(5):  # Send data for about 20 seconds (5 cycles of 4 seconds each)
        await send_data(client, 1)  # Send value of 1
        await asyncio.sleep(2)  # Wait for 2 seconds
        await send_data(client, 0)  # Send value of 0
        await asyncio.sleep(2)  # Wait for 2 seconds


#######################################################################################
class DevicePortal(tk.Toplevel):
    def __init__(self, parent: App):
        super().__init__(parent)

        self.geometry("300x300")
        self.parent = parent
        self.parent.withdraw() # hide App until connected
        self.search()
        
        ttk.Button(self,text="Scan for devices",command=self.search,default='active').place(relx=.5, rely=0.20, anchor="center")
        ttk.OptionMenu(self, parent.deviceSelection, 'Click here to pick a device', *devices).place(relx=.5, rely=0.35, anchor="center")
        ttk.Button(self, text='Connect', command=self.connect, default='active').place(relx=.5, rely=0.5, anchor="center")

    def search(self):
        asyncio.run(scan())

    def connect(self):
        self.parent.connect()
        self.destroy()
        self.parent.deiconify() # reveal App

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("LED Blinker")
        self.geometry("300x300")
        self.led = tk.BooleanVar()
        self.deviceSelection = tk.StringVar()

        check1 = ttk.Checkbutton(self, text ='Toggle LED', variable=self.led, command=self.update_led).place(relx=.5, rely=0.35, anchor="center")
        button1 = ttk.Button(self, text = 'Send invalid', command=self.send_invalid).place(relx=.5, rely=0.5, anchor="center")
        button2 = ttk.Button(self, text = 'Disconnect', default='active', command=self.disconnect).place(relx=.5, rely=0.65, anchor="center")
        #check1.pack()

        DevicePortal(self) # and this

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.disconnect()

    def connect(self):
        for deviceC in devices:
            if deviceC.name == self.deviceSelection.get():
                print("Connecting to device")
                asyncio.run(connectBLE(deviceC))

    @detached_callback
    def update_led(self):
        global toggler
        toggler = self.led.get()
        #asyncio.run(updateLED())

    def disconnect(self):
        self.ser.close()

        DevicePortal(self) # display portal to reconnect

    def send_invalid(self):
       self.write(bytes([0x10]))

    def write(self, b: bytes):
        try:
            self.ser.write(b)
            if int.from_bytes(self.ser.read(), 'big') == S_ERR:
                showerror('Device Error', 'The device reported an invalid command.')
        except SerialException:
            showerror('Serial Error', 'Write failed.')


if __name__ == '__main__':
    with App() as app: 
        app.mainloop()
