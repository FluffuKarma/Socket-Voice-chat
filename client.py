import socket
import threading
import pyaudio
import tkinter as tk
import time
import sys
from tkinter import messagebox

class Client(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent

        self.s = None
        self.connection_active=False

        self.chunk_size = 1024 # 512
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 20000

        self.playing_stream = None
        self.recording_stream = None

        #audio devices
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        self.audio_devices=[{},{}]

        for i in range(0, numdevices):
                if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    self.audio_devices[0][p.get_device_info_by_host_api_device_index(0,i).get('name')] = p.get_device_info_by_host_api_device_index(0,i).get('index')
                else:
                    self.audio_devices[1][p.get_device_info_by_host_api_device_index(0,i).get('name')] = p.get_device_info_by_host_api_device_index(0,i).get('index')

        self.target_ip = "192.168.2.245"
        self.target_port = int(80)

        #gui
        self.IP_text_var = tk.StringVar(parent, value=self.target_ip)
        self.IP_text = tk.Entry(parent, textvariable=self.IP_text_var)
        self.IP_text.pack()

        self.Input_device = tk.StringVar(parent)
        self.Input_device.set(list(self.audio_devices[0])[0]) # default value
        self.Input_device_dropdown = tk.OptionMenu(parent, self.Input_device, *self.audio_devices[0].keys())
        self.Input_device_dropdown.pack()

        self.Output_device = tk.StringVar(parent)
        self.Output_device.set(list(self.audio_devices[1])[0]) # default value
        self.Output_device_dropdown = tk.OptionMenu(parent, self.Output_device, *self.audio_devices[1].keys())
        self.Output_device_dropdown.pack()

        self.connect_button = tk.Button(parent, text="CONNECT", command=self.connectTo)
        self.connect_button.pack()
    
    def printText(self):
        while True:
            print(self.IP_text_var.get())
            time.sleep(1)

    def receive_server_data(self):
        while self.connection_active==True:
            try:
                data = self.s.recv(1024)
                self.playing_stream.write(data)
            except:
                pass


    def send_data_to_server(self):
        while self.connection_active==True:
            try:
                data = self.recording_stream.read(1024)
                self.s.sendall(data)
            except:
                pass

    def connectTo(self):
        connect_thread = threading.Thread(target=self.connect(2)).start()

    def connect(self, connection_retries):
        self.connect_button["state"]="disable"
        if self.connection_active==False:
            for i in range(connection_retries):
                try:
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.s.connect((str(self.IP_text_var.get()), self.target_port))

                    self.connection_active=True
                    
                    # initialise microphone recording
                    self.p = pyaudio.PyAudio()
                    self.playing_stream = self.p.open(format=self.audio_format, channels=self.channels, rate=self.rate, output=True, frames_per_buffer=self.chunk_size, output_device_index=self.audio_devices[1][self.Output_device.get()])
                    self.recording_stream = self.p.open(format=self.audio_format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk_size, input_device_index=self.audio_devices[0][self.Input_device.get()])

                    # start threads
                    receive_thread = threading.Thread(target=self.receive_server_data).start()
                    send_thread = threading.Thread(target=self.send_data_to_server).start()

                    self.connect_button.configure(fg='green')

                    break
                except:
                    print("Couldn't connect to server")
                    pass
        else:
            self.s.close()
            self.connect_button.configure(fg='black')
            self.connection_active=False

        self.connect_button["state"]="active"

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()
        sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    Client(root)
    root.mainloop()
