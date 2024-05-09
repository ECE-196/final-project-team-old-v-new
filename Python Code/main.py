from __future__ import annotations
from threading import Thread, Lock
from bluetoothESP import BLEAdapter
import asyncio

import sys
import math
import time
import tkinter as tk
import tkinter.ttk as ttk
from threading import Thread, Lock
from tkinter.messagebox import showerror

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

class App(tk.Tk):
    _lock: Lock = Lock()
    
    def __init__(self):
        super().__init__()
        
        self.title("Snowboard")
        self.geometry("800x600")
        self.calibration = []
        self.connectblue = tk.IntVar()

        self.output = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.parsedOutput = [0.0,0.0,0.0]
        self.calibratedOutput = [0.0, 1.0, 2.0]
        self.currentTime = 0
        self.gyroAngleX = 0
        self.gyroAngleY = 0
        self.yaw = 0.0

        self.checkButton = tk.Checkbutton(self, text="Connect to Bluetooth",  variable=self.connectblue, command=lambda : self.toggle_bluetooth(self.connectblue))
        self.checkButton.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
        ttk.Button(self, text='calibrate', command=self.update_calibration).pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
        self.display = tk.Text(self, height=5, width=80, state=tk.DISABLED)
        self.console = tk.Text(self, height=10, width=80, state=tk.DISABLED)
        self.console.pack(side=tk.BOTTOM, fill="both", expand=True, anchor=tk.W,padx=50, pady=10)
        tk.Label(self, text="Console").pack(side=tk.BOTTOM, anchor=tk.W,padx=50)
        self.display.pack(side=tk.BOTTOM, anchor=tk.W,padx=50, pady=10)
        tk.Label(self, text="Display").pack(side=tk.BOTTOM, anchor=tk.W,padx=50)
        sys.stdout = ConsoleRedirector(self.console)
        
        self.pitch = tk.Label(self,  text=self.toString("Pitch", 0))
        self.pitch.pack(side=tk.TOP, anchor = tk.W, padx = 10, pady=10)
        self.yaw = tk.Label(self, text=self.toString("Yaw", 1))
        self.yaw.pack(side=tk.TOP, anchor = tk.W,  padx = 10, pady=10)
        self.roll = tk.Label(self, text=self.toString("Roll", 2))
        self.roll.pack(side=tk.TOP, anchor = tk.W,  padx = 10, pady=10)
        
        self.adapter = BLEAdapter()
        self.update_text()
        self.mainloop()

    @detached_callback
    def update_calibration(self):
        with self._lock:
            popup_window = tk.Toplevel(self)
            popup_window.geometry("300x200")

            self.displayCalibration(popup_window,tk.TOP,tk.N,0,10)
    
            close_button = tk.Button(popup_window, text="Close", command=popup_window.destroy)
            close_button.pack(side=tk.TOP, anchor=tk.N, padx=10, pady=10)
            self.pitch.config(text=self.toString("Pitch", 0))
            self.yaw.config(text=self.toString("Yaw", 1))
            self.roll.config(text=self.toString("Roll", 2))
            return
    
    
    @detached_callback
    def toggle_bluetooth(self, state):
        with self._lock:
            if self.connectblue.get()==1:
                print(f"Creating Scanner Instance...") 
                result = asyncio.run(self.adapter.scan_and_connect())
                if (result):
                    self.read()
                    return
                else:
                    self.connectblue.set(0)  
           
            
            else:
                self.disconnect_bluetooth() 
                print(f"Disconnected from Bluetooth Device") 
            
            return  
    
    @detached_callback
    def read(self):
        global data
        with self._lock:
            asyncio.run(self.adapter.read_data())
            for i in range(len(self.adapter.data)):
                self.output[i] = self.adapter.data[i]
            self.ParseOutput()
            self.after(500,self.read)  
        return

    @detached_callback
    def write(self):
        return

    @detached_callback
    def disconnect_bluetooth(self):
        with self._lock:
            return

    @detached_callback
    def update_text(self):
        with self._lock:
            self.display.config(state=tk.NORMAL)  
            self.display.delete("1.0", tk.END)  
            self.display.insert(tk.END, self.parsedOutput)  
            self.display.config(state=tk.DISABLED)
            self.after(500,self.update_text)  
            
    
    def ParseOutput(self):
        result = []
        AccX = self.output[0]
        AccY = self.output[1]
        AccZ = self.output[2]
        GyroX = self.output[3]
        GyroY = self.output[4]
        GyroZ = self.output[5]
        accAngleX = (math.atan(AccY / math.sqrt(pow(AccX, 2) + pow(AccZ, 2))) * 180 / math.pi) - 0.58
        accAngleY = (math.atan(-1 * AccX / math.sqrt(pow(AccY, 2) + pow(AccZ, 2))) * 180 / math.pi) + 1.58
        
        if (self.currentTime == 0):
            self.currentTime = time.time()
        previousTime = self.currentTime
        self.currentTime = time.time()
        elapsedTime = (self.currentTime - previousTime)  
        
        # Correct output with Error values
        GyroX = GyroX + 0.56
        GyroY = GyroY - 2
        GyroZ = GyroZ + 0.79

        # Calculate gyro angles
        self.gyroAngleX = self.gyroAngleX + GyroX * elapsedTime
        self.gyroAngleY = self.gyroAngleY + GyroY * elapsedTime
        self.yaw += GyroZ * elapsedTime

        # Complementary filter - combine accelerometer and gyro angle values
        roll = 0.96 * gyroAngleX + 0.04 * accAngleX
        pitch = 0.96 * gyroAngleY + 0.04 * accAngleY
        
        self.parsedOutput[0] = pitch
        self.parsedOutput[1] = yaw
        self.parsedOutput[2] = roll
        return
        
    def displayCalibration(self,window,sd,ac,px,py):
        window.pitch = tk.Label(window, text=self.toString("Pitch", 0))
        window.pitch.pack(side=sd, anchor=ac, padx = px, pady=py)
        window.yaw = tk.Label(window, text=self.toString("Yaw", 1))
        window.yaw.pack(side=sd, anchor=ac, padx = px,pady=py)
        window.roll = tk.Label(window, text=self.toString("Roll", 2))
        window.roll.pack(side=sd, anchor=ac, padx = px, pady=py)
            
    def toString(self,text,i):
        return text + ": " + str(self.calibratedOutput[i])
    
    
if __name__ == "__main__":
    app = App()