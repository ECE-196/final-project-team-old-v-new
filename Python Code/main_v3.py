from __future__ import annotations
from threading import Thread, Lock
from tkinter import messagebox
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

notes_listbox = None

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

# UI STUFF
def create_gradient_background(canvas, color1, color2):
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    canvas.create_rectangle(0, 0, width, height, fill=color1, width=0)
    for i in range(height):
        r = int(color1[1:3], 16) + int(i * (int(color2[1:3], 16) - int(color1[1:3], 16)) / height)
        g = int(color1[3:5], 16) + int(i * (int(color2[3:5], 16) - int(color1[3:5], 16)) / height)
        b = int(color1[5:7], 16) + int(i * (int(color2[5:7], 16) - int(color1[5:7], 16)) / height)
        color = f'#{r:02x}{g:02x}{b:02x}'
        canvas.create_line(0, i, width, i, fill=color)

# UI STUFF


# Interpretation Setup###############################
def openNotes():
    global notes_listbox
    # Create a new window
    notes_window = tk.Toplevel()
    notes_window.title("Feedback Notes")
    notes_window.geometry("650x450")

    # Create a custom font
    custom_font = ("Helvetica", 16)

    # Create a Listbox widget to display the notes with the custom font
    notes_listbox = tk.Listbox(notes_window, font=custom_font)
    notes_listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(10, 20))  # Add padx and pady for padding

    # Create a Scrollbar widget for vertical scrolling
    scrollbar_y = ttk.Scrollbar(notes_window, orient="vertical", command=notes_listbox.yview)
    scrollbar_y.pack(side="right", fill="y")

    # Configure the Listbox widget to use the Scrollbar
    notes_listbox.config(yscrollcommand=scrollbar_y.set)

    try:
        # Try to open the text file and read its contents line by line
        with open("Python Code/feedback.txt", "r") as file:
            for line in file:
                notes_listbox.insert(tk.END, line.strip())  # Strip newline characters from each line
    except FileNotFoundError:
        # If the file is not found, create it and display a message
        with open("Python Code/feedback.txt", "w") as file:
            file.write("No feedback notes found.")
            notes_listbox.insert(tk.END, "No feedback notes found.")

def addNote(number):
    global notes_listbox  # Accessing the global notes_listbox variable
    # Define an array of note strings
    notes = [
        "Ease up on the throttle, slow down and regain control!",
        "Don't rush, find your rhythm and glide smoothly!",
        "Lead with your knees, not your nose, and maintain balance!",
        "Relax those legs, let them absorb the bumps!",
        "Keep your knees bent and ready to adjust!",
        "Don't lock those knees, keep them loose and flexible!",
        "Stay smooth and steady, don't rush your turns!",
        "Mind your speed, it's all about control!",
        "Slow it down, keep your movements deliberate and precise!",
        "Shoulders parallel with your board, stay aligned for stability!",
        "Stay centered, don't let your shoulders lead the way!",
        "Relax your upper body, let your legs do the work!",
        "Keep those shoulders square, don't twist too much!",
        "Balance is key, keep your weight evenly distributed!",
        "Maintain a fluid motion, don't tense up!",
        "Stay loose and relaxed, it's all about flow!",
        "Keep your movements smooth and controlled!",
        "Stay centered and focused, keep your eyes on the path ahead!",
        "Glide with grace, don't force it!",
        "Let the board do the work, just guide it with your movements!"
    ]

    # Check if the provided number is within the range of the notes array
    if 0 <= number < len(notes):
        # Open the feedback.txt file in append mode
        with open("feedback.txt", "a") as file:
            # Get the content of the note from the notes array
            new_note = notes[number]
            # Write the new note to the file
            file.write(new_note + "\n")
        # Add the new note to the notes_listbox
        notes_listbox.insert(tk.END, new_note)
    else:
        print("Invalid note number. Please provide a valid number within the range of available notes.")

# Interpretation Setup###############################


def build_app():
    global app, display, console,connectblue, calibration_F,calibration_B,prevAccel,velocity,output_F,calibratedOutput_F,output_B,calibratedOutput_B, left,right
    app = tk.Tk()
    connectblue = tk.IntVar()
    app.title("Snowboard Support System")
    app.geometry("800x600")

    ######################################################################
    app.configure(bg="#BFEFFF")  # Baby blueish color
    #app.configure(bg="white")  # Set background color to white
    style = ttk.Style()
    style.configure("Blue.TLabel", background="#BFEFFF")    
    #style.configure("Blue.TLabel", background="white") 

    # Define the blueish background color
    button_bg_color = 'red'

    # Configure the style for the button
    style.configure('Red.TButton', background=button_bg_color, bordercolor=button_bg_color, lightcolor=button_bg_color, darkcolor=button_bg_color)

    button_bg_color = "#800080"

    # Configure the style for the button
    style.configure('Purple.TButton', background=button_bg_color, bordercolor=button_bg_color, lightcolor=button_bg_color, darkcolor=button_bg_color)

    ######################################################################

    label = ttk.Label(app, text='Snowboard Support System (SSS)', font=("Helvetica", 24, "bold"),style="Blue.TLabel")
    label.pack(ipadx=10, ipady=10)
    
    button_frame = tk.Frame(app, background="#BFEFFF")
    # button_frame = tk.Frame(app, background="white")
    button_frame.pack()

    notesButton = ttk.Button(button_frame,text="Feedback Notes", command=openNotes)
    notesButton.pack(side=tk.RIGHT, padx=10, pady=10)

    connectButton = ttk.Button(button_frame, text="Connect to Bluetooth", command=lambda:asyncio.create_task(connect_bluetooth()), style="Purple.TButton")
    connectButton.pack(side=tk.RIGHT, padx=10, pady=10)

    disconnectButton = ttk.Button(button_frame, text="Disconnect", command=lambda:asyncio.create_task(disconnect()),style="Red.TButton")
    disconnectButton.pack(side=tk.RIGHT, padx=10, pady=10)
    
    calibrateR = ttk.Button(button_frame, text='Calibrate Right', command=lambda:asyncio.create_task(calibrateRight()))
    calibrateR.pack(side=tk.RIGHT, padx=10, pady=10)

    calibrateL = ttk.Button(button_frame, text='Calibrate Left', command=lambda:asyncio.create_task(calibrateLeft()))
    calibrateL.pack(side=tk.RIGHT, padx=10, pady=10)

    
    left = tk.Label(text=toString(0))
    left.pack(side=tk.TOP, anchor = tk.W, padx = 10)
    right = tk.Label(text=toString(1))
    right.pack(side=tk.TOP, anchor = tk.W,  padx = 10) 
        
    display = tk.Text(height=4, width=80, state=tk.DISABLED, background="black", foreground="lime", font=("Helvetica", 18) )
    #display.config(state=tk.NORMAL)  

    # COMMENT HERE
    #display.insert(tk.END, "Hello World: How does this look? 18.9999 6.9999. 9.8686") 
    console = tk.Text(height=8, width=80, state=tk.DISABLED)
    console.pack(side=tk.BOTTOM, fill="both", expand=True, anchor=tk.W,padx=20,pady=(10,15))
    tk.Label(app,text="Console",font=("Helvetica", 16, "underline"), bg="#BFEFFF").pack(side=tk.BOTTOM, anchor=tk.W,padx=20)
    display.pack(side=tk.BOTTOM, anchor=tk.W,padx=20, pady=10)
    tk.Label(app,text="Display",font=("Helvetica", 16, "underline"), bg="#BFEFFF").pack(side=tk.BOTTOM, anchor=tk.W,padx=20)
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
        messagebox.showerror("Bluetooth Connection", "You are already connected to the devices!")
        
        
  
async def disconnect():
    global adapter, stop, disconnect
    if adapter.isConnected == True:
        adapter.SERVICE_F = 0
        adapter.SERVICE_B = 0
        adapter.disconnect = True
        await adapter.disconnect_and_quit()
    else:
        print(f"devices already disconnected")
        messagebox.showerror("Bluetooth Connection", "You have already disconnected from the devices!")
       
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
        await asyncio.sleep(1.5)

async def write_back():
    global adapter, buzz_B,freq_B
    while (stop ==False):
        if (adapter.disconnect  == True):
            break
        if (adapter.client_F.is_connected and adapter.client_B.is_connected and buzz_B == True):
            asyncio.create_task(adapter.send_data("Back",1,1))
        await asyncio.sleep(1.5)

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
        freq_F = 60 + 180 * (output_F[0] - 0.8*calibratedOutput_L[0])/math.fabs(calibratedOutput_L[0]-0.8*calibratedOutput_L[0])
    elif (calibratedOutput_R[0] > 0 and output_F[0] > 0.8*calibratedOutput_R[0]):
        buzz_F = True
        freq_F = 60 + 180 * (output_F[0] - 0.8*calibratedOutput_R[0])/math.fabs(calibratedOutput_R[0]-0.8*calibratedOutput_R[0])
    elif (calibratedOutput_L[0] < 0 and output_F[0] < 0.8*calibratedOutput_L[0]):
        buzz_F = True
        freq_F = 60 + 180 * (0.8*calibratedOutput_L[0] - output_F[0])/math.fabs(calibratedOutput_L[0]-0.8*calibratedOutput_L[0])
    elif (calibratedOutput_R[0] < 0 and output_F[0] < 0.8*calibratedOutput_R[0]):
        buzz_F = True
        freq_F = 60 + 180 * (0.8*calibratedOutput_R[0] - output_F[0])/math.fabs(calibratedOutput_R[0]-0.8*calibratedOutput_R[0])
    else:
        buzz_F = False  
        freq_F = 60

    return

async def updateBuzzerState_B():
    global adapter, buzz_B, output_B, output_F, SAFE_VELOCITY
    if output_B[5] > 0.8*SAFE_VELOCITY:     #output_F[5] = vy
        buzz_B = True
        freq_B = 60 + 180 * (output_B[5] - 0.8*SAFE_VELOCITY)/(SAFE_VELOCITY-0.8*SAFE_VELOCITY)
    else:
        buzz_B= False  

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
    return side + ":\n" + "Pitch" + ":  " + str(calibratedOutput[2])  + "/  Yaw" + ":  " + str(calibratedOutput[1]) + "/ Roll" + ":  " + str(calibratedOutput[0]) + "\n"


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