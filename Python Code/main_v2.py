from __future__ import annotations
from threading import Thread, Lock
from bluetoothESP import BLEAdapter
import asyncio

import sys
import math
import time
import threading
import tkinter as tk
import tkinter.ttk as ttk
from threading import Thread, Lock
from tkinter.messagebox import showerror

LAMBDA = 10e-6
ALPHA = 0.98  # Weight for the gyroscope data
SAFE_VELOCITY = 3
dt = 0.05
calibratedOutput_L = []
calibratedOutput_R = []

buzz_F = False
buzz_B = False
left = 0
right = 0
freq_F = 60
freq_B = 60
output_F = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
output_B = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
calibratedOutput_L = [0.0, 0.0, 0.0]
calibratedOutput_R = [0.0, 0.0, 0.0]
stop = False
adapter = BLEAdapter()
_Lock: Lock = Lock()
def detached_callback(f):
    return lambda *args, **kwargs: Thread(target=f, args=args, kwargs=kwargs).start()
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.config(state=tk.NORMAL)  
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)  
        self.text_widget.config(state=tk.DISABLED)

def build_app():
    global app, display, console,connectblue, calibration_F,calibration_B,prevAccel,velocity,output_F,calibratedOutput_F,output_B,calibratedOutput_B, left,right
    app = tk.Tk()
    connectblue = tk.IntVar()
    app.title("Snowboard Support System")
    app.geometry("800x600")
    
    connectButton = ttk.Button(app, text="Connect to Bluetooth", command=lambda:asyncio.create_task(connect_bluetooth()))
    connectButton.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
    
    disconnectButton = ttk.Button(app, text="Disconnect", command=lambda:asyncio.create_task(disconnect()))
    disconnectButton.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
      
    calibrateL = ttk.Button(app, text='Calibrate Left', command=lambda:asyncio.create_task(calibrateLeft()))
    calibrateL.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)

    calibrateR = ttk.Button(app, text='Calibrate Right', command=lambda:asyncio.create_task(calibrateRight()))
    calibrateR.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
    
    left = tk.Label(text=toString(0))
    left.pack(side=tk.TOP, anchor = tk.W, padx = 10)
    right = tk.Label(text=toString(1))
    right.pack(side=tk.TOP, anchor = tk.W,  padx = 10) 
        
    display = tk.Text(height=4, width=80, state=tk.DISABLED)
    console = tk.Text(height=10, width=80, state=tk.DISABLED)
    console.pack(side=tk.BOTTOM, fill="both", expand=True, anchor=tk.W,padx=20)
    tk.Label(app,text="Console").pack(side=tk.BOTTOM, anchor=tk.W,padx=20)
    display.pack(side=tk.BOTTOM, anchor=tk.W,padx=20, pady=10)
    tk.Label(app,text="Display").pack(side=tk.BOTTOM, anchor=tk.W,padx=20)
    sys.stdout = ConsoleRedirector(console)
    
    app.protocol("WM_DELETE_WINDOW", on_close)

#App frontend <--> BLEAdapter controls    
async def connect_bluetooth():
    global adapter, stop
    adapter.disconnect = False
    if adapter.isConnected == False:
        await adapter.scan_and_connect()
        if adapter.isConnected == True:
            asyncio.create_task(read())
            await write_front()
            await write_back()
    else:
        print("Already connected")
        
  
async def disconnect():
    global adapter, stop, disconnect
    if adapter.isConnected == True:
        adapter.SERVICE_F = 0
        adapter.SERVICE_B = 0
        adapter.disconnect = True
        await adapter.disconnect_and_quit()
    else:
        print(f"devices already disconnected")
       
async def read():
    global adapter, stop,output_F,output_B
    while (stop ==False):
        if (adapter.disconnect  == True):
            break
        if (adapter.client_F.is_connected and adapter.client_B.is_connected):
            await adapter.read_data()
            if (adapter.data_available):  
                try:
                    for i in range(len(adapter.data_F)):
                        if len(adapter.data_F) > 0:
                            output_F[i] = adapter.data_F[i]
                        if len(adapter.data_B) > 0:
                            output_B[i] = adapter.data_B[i]
                    asyncio.create_task(updateBuzzerState_F())
                    asyncio.create_task(updateBuzzerState_B())
                    asyncio.create_task(update_display())
                except Exception as e:
                    print("Error in read():", e)
        else:
            adapter.disconnect = True
            await adapter.disconnect_and_quit() 
            adapter.disconnect = False
            i = 1
            while (adapter.isConnected == False):
                print("reconnecting...",i)
                await adapter.scan_and_connect()
                i+=1
        await asyncio.sleep(0.05)
    
async def write_front():
    global adapter, buzz_F,freq_F
    while (stop ==False):
        if (adapter.disconnect  == True):
            break
        if (adapter.client_F.is_connected and adapter.client_B.is_connected and buzz_F == True):
            asyncio.create_task(adapter.send_data("Front",1,1))
        await asyncio.sleep(1/freq_F)

async def write_back():
    global adapter, buzz_B,freq_B
    while (stop ==False):
        if (adapter.disconnect  == True):
            break
        if (adapter.client_F.is_connected and adapter.client_B.is_connected and buzz_B == True):
            asyncio.create_tast(adapter.send_data("Back",1,1))
        await asyncio.sleep(1/freq_B)

async def calibrateLeft():
    global calibratedOutput_L,output_F, left
    popup_window = tk.Toplevel(app)
    popup_window.geometry("300x200")
    for i in range(3):
        calibratedOutput_L[i] = output_F[i]
        displayCalibration(popup_window,tk.TOP,tk.N,0,10)
        close_button = tk.Button(popup_window, text="Close", command=popup_window.destroy)
        close_button.pack(side=tk.TOP, anchor=tk.N, padx=10, pady=10)
    left.config(text=toString(0))
    return

async def calibrateRight():
    global calibratedOutput_R,output_F, right
    popup_window = tk.Toplevel(app)
    popup_window.geometry("300x200")
    for i in range(3):
        calibratedOutput_R[i] = output_F[i]
        displayCalibration(popup_window,tk.TOP,tk.N,0,10)
        close_button = tk.Button(popup_window, text="Close", command=popup_window.destroy)
        close_button.pack(side=tk.TOP, anchor=tk.N, padx=10, pady=10)
    right.config(text=toString(1))
    return


#Data Parsing Logics
async def updateBuzzerState_F():
    global adapter, buzz_F,calibratedOutput_L, calibratedOutput_R, output_F
    if (calibratedOutput_L[0] == 0 or calibratedOutput_R[0] == 0):   #check for pitch, positive y axis is front
        return       
    if (calibratedOutput_L[0] > 0 and output_F[0] > 0.8*calibratedOutput_L[0]):
        buzz_F = True
        freq_F = 60 + 180 * (output_F[0] - 0.8*calibratedOutput_L[0])/math.abs(calibratedOutput_L[0]-0.8*calibratedOutput_L[0])
    elif (calibratedOutput_R[0] > 0 and output_F[0] > 0.8*calibratedOutput_R[0]):
        buzz_F = True
        freq_F = 60 + 180 * (output_F[0] - 0.8*calibratedOutput_R[0])/math.abs(calibratedOutput_R[0]-0.8*calibratedOutput_R[0])
    elif (calibratedOutput_L[0] < 0 and output_F[0] < 0.8*calibratedOutput_L[0]):
        buzz_F = True
        freq_F = 60 + 180 * (0.8*calibratedOutput_L[0] - output_F[0])/math.abs(calibratedOutput_L[0]-0.8*calibratedOutput_L[0])
    elif (calibratedOutput_R[0] < 0 and output_F[0] < 0.8*calibratedOutput_R[0]):
        buzz_F = True
        freq_F = 60 + 180 * (0.8*calibratedOutput_R[0] - output_F[0])/math.abs(calibratedOutput_R[0]-0.8*calibratedOutput_R[0])
    else:
        buzz_F = False  
        freq_F = 60

    return

async def updateBuzzerState_B():
    global adapter, buzz_B, output_B, output_F, SAFE_VELOCITY
    if output_F[5] > 0.8*SAFE_VELOCITY:     #output_F[5] = vy
        buzz_B = True
        freq_B = 60 + 180 * (output_F[5] - 0.8*SAFE_VELOCITY)/(SAFE_VELOCITY-0.8*SAFE_VELOCITY)
    else:
        buzz_F = False  

    return

#displays    
async def update_display():
    global display,output_B, output_F
    pyr_B = ["{:.2f}".format(output_B[2]),"{:.2f}".format(output_B[1]),"{:.2f}".format(output_B[0]), "{:.2f}".format(output_B[5])]
    pyr_F = ["{:.2f}".format(output_F[2]),"{:.2f}".format(output_F[1]),"{:.2f}".format(output_F[0]), "{:.2f}".format(output_F[5])]
    display.config(state=tk.NORMAL)  
    display.delete("1.0", tk.END)  
    display.insert(tk.END, "Front: ") 
    display.insert(tk.END, pyr_F)  
    display.insert(tk.END, "\n") 
    display.insert(tk.END, "Back: ") 
    display.insert(tk.END, pyr_B)
    display.insert(tk.END, "\n")   
    display.config(state=tk.DISABLED)
    
def displayCalibration(window,sd,ac,px,py):
    window.left = tk.Label(window, text=toString(0))
    window.left.pack(side=sd, anchor=ac, padx = px, pady=py)
    window.right = tk.Label(window, text=toString(1))
    window.right.pack(side=sd, anchor=ac, padx = px,pady=py)


def toString(i):  #0 is front, 1 is back
    global calibratedOutput_L, calibratedOutput_R
    calibratedOutput = calibratedOutput_L if i == 0 else calibratedOutput_R
    side = "Left" if i == 0 else "Right"
    return side + ":\n" + "Pitch" + ":  " + str(calibratedOutput[2])  + "Yaw" + ":  " + str(calibratedOutput[1]) + "Roll" + ":  " + str(calibratedOutput[0]) + "\n"


# Tkinter backend Controls
def on_close():
    global stop
    stop = True
    print("Closing...")
    
async def show():
    while (stop ==False):
        app.update()
        await asyncio.sleep(0.01)
    
async def main():
    global stop
    build_app()
    await show()
    app.destroy()
    
asyncio.run(main())