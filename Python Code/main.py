from __future__ import annotations
from threading import Thread, Lock
from bluetoothESP import BLEAdapter
import asyncio

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

LAMBDA = 10e-6
dt = 0.05

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
        
        self.title("Snowboard Support System")
        self.geometry("800x600")
        self.calibration_F = []
        self.calibration_B = []
        self.connectblue = tk.IntVar()
        self.prevAccel = 0
        self.velocity = 0

        self.output_F = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.parsedOutput_F = [0.0,0.0,0.0]
        self.calibratedOutput_F = [0.0, 0.0, 0.0]
        self.output_B = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.parsedOutput_B = [0.0,0.0,0.0]
        self.calibratedOutput_B = [0.0, 0.0, 0.0]

        self.checkButton = tk.Checkbutton(self, text="Connect to Bluetooth",  variable=self.connectblue, command=lambda : self.toggle_bluetooth(self.connectblue))
        self.checkButton.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
        self.checkButton.place(relx=.8, rely=0.2, anchor="center")
        
        calibrateL = ttk.Button(self, text='Calibrate Forward', command=self.update_calibration)
        calibrateL.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
        calibrateL.place(relx=.40, rely=0.2, anchor="center")
        
        calibrateR = ttk.Button(self, text='Calibrate Back', command=self.update_calibration)
        calibrateR.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
        calibrateR.place(relx=.60, rely=0.2, anchor="center")
        
        # Here for testing purposes for the buzzers
        buzzL = ttk.Button(self, text='Forward Buzzer', command=self.writeFront)
        buzzL.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
        buzzL.place(relx=.40, rely=0.1, anchor="center")

        buzzR = ttk.Button(self, text='Back Buzzer', command=self.writeBack)
        buzzR.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=10)
        buzzR.place(relx=.60, rely=0.1, anchor="center")

        self.display = tk.Text(self, height=5, width=80, state=tk.DISABLED)
        self.console = tk.Text(self, height=10, width=80, state=tk.DISABLED)
        self.console.pack(side=tk.BOTTOM, fill="both", expand=True, anchor=tk.W,padx=50, pady=10)
        tk.Label(self, text="Console").pack(side=tk.BOTTOM, anchor=tk.W,padx=50)
        self.display.pack(side=tk.BOTTOM, anchor=tk.W,padx=50, pady=10)
        tk.Label(self, text="Display").pack(side=tk.BOTTOM, anchor=tk.W,padx=50)
        sys.stdout = ConsoleRedirector(self.console)
        
        self.front = tk.Label(self,  text=self.toString(0))
        self.front.pack(side=tk.TOP, anchor = tk.W, padx = 10, pady=10)
        self.back = tk.Label(self, text=self.toString(1))
        self.back.pack(side=tk.TOP, anchor = tk.W,  padx = 10, pady=10)
        
        self.adapter = BLEAdapter()
        self.update_text()
        self.mainloop()

    @detached_callback
    def update_calibration(self):
        with self._lock:
            popup_window = tk.Toplevel(self)
            popup_window.geometry("300x200")

            for i in range(3):
                self.calibratedOutput_F[i] = self.parsedOutput_F[i]
                self.calibratedOutput_B[i] = self.parsedOutput_B[i]
            self.displayCalibration(popup_window,tk.TOP,tk.N,0,10)
    
            close_button = tk.Button(popup_window, text="Close", command=popup_window.destroy)
            close_button.pack(side=tk.TOP, anchor=tk.N, padx=10, pady=10)
            self.front.config(text=self.toString(0))
            self.back.config(text=self.toString(1))
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
                    self.adapter.SERVICE_F = 0
                    self.adapter.SERVICE_B = 0
                   
            else:
                self.disconnect_bluetooth() 
                self.velocity = 0
                self.prevAccel = 0
                self.calibratedOutput_F = [0.0,0.0,0.0]
                self.calibratedOutput_B = [0.0,0.0,0.0]
                print(f"Disconnected from Bluetooth Device") 
            
            return  
    
    @detached_callback
    def read(self):
        global data
        with self._lock:
            self.prevAccel = self.output_B[0]
            asyncio.run(self.adapter.read_data())
            for i in range(len(self.adapter.data_F)):
                if (len(self.adapter.data_F) > 0):
                    self.output_F[i] = self.adapter.data_F[i]
                if (len(self.adapter.data_B) > 0):
                    self.output_B[i] = self.adapter.data_B[i]
            self.ParseOutput(0)
            self.ParseOutput(1)
            self.after(50,self.read)  
        return

    # Methods to send signal to buzzer (right now only short beeps)
    @detached_callback
    def writeFront(self):
            asyncio.run(self.adapter.send_data("front",1,1))
            return

    @detached_callback
    def writeBack(self):
            asyncio.run(self.adapter.send_data("back",1,1))
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
            self.display.insert(tk.END, "Front: ") 
            self.display.insert(tk.END, self.parsedOutput_F)  
            self.display.insert(tk.END, "\n") 
            self.display.insert(tk.END, "Back: ") 
            self.display.insert(tk.END, self.parsedOutput_B)
            self.display.insert(tk.END, "\n")   
            self.display.insert(tk.END, "Velocity: ") 
            self.display.insert(tk.END, self.velocity)
            self.display.insert(tk.END, "\n")  
            self.display.config(state=tk.DISABLED)
            self.after(50,self.update_text)  
            
    
    def ParseOutput(self, i):
        output = self.output_F if i == 0 else self.output_B
        parsedOutput = self.parsedOutput_F if i == 0 else self.parsedOutput_B
        AccX = output[0]
        AccY = output[1]
        AccZ = output[2]
        GyroX = output[3]
        GyroY = output[4]
        GyroZ = output[5]
        pitch = (math.atan2(AccY, math.sqrt(pow(AccX, 2) + pow(AccZ, 2))) )*180/math.pi
        roll = math.atan2(-AccX, AccZ)*180/math.pi
        dt = 0.05  # Time between readings (adjust as needed)
        yaw = parsedOutput[1] + GyroZ * dt
        parsedOutput[0] = pitch
        parsedOutput[1] = yaw
        parsedOutput[2] = roll

    def updateVelocity(self):
        global dt
        self.velocity += (output_B[0] + prevAccel) * dt / 2.0

        
    def displayCalibration(self,window,sd,ac,px,py):
        window.front = tk.Label(window, text=self.toString(0))
        window.front.pack(side=sd, anchor=ac, padx = px, pady=py)
        window.back = tk.Label(window, text=self.toString(1))
        window.back.pack(side=sd, anchor=ac, padx = px,pady=py)
            
    def toString(self,i):  #0 is front, 1 is back
        calibratedOutput = self.calibratedOutput_F if i == 0 else self.calibratedOutput_B
        side = "Front" if i == 0 else "Back"
        return side + ":\n" + "Pitch" + ":  " + str(calibratedOutput[0])  + "Yaw" + ":  " + str(calibratedOutput[1]) + "Roll" + ":  " + str(calibratedOutput[2])
    
    
if __name__ == "__main__":
    app = App()

    
    
