import os
import clr
import sys
import time
import tkinter as tk
from tkinter import messagebox

# Ajouter les chemins complets vers les assemblées Thorlabs
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.KCube.SolenoidCLI.dll")

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.GenericMotorCLI import GenericMotorCLI
from Thorlabs.MotionControl.KCube.SolenoidCLI import KCubeSolenoid, SolenoidStatus
from System import Decimal  # nécessaire pour les unités du monde réel

class ShutterControlApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Shutter Control")

        self.serial_no = "68800404"  # Remplacez cette ligne par le numéro de série de votre appareil
        self.device = None

        self.create_widgets()

        # Initialisation de l'API Thorlabs Kinesis
        try:
            DeviceManagerCLI.BuildDeviceList()

            # Liste des dispositifs connectés          
            self.device = KCubeSolenoid.CreateKCubeSolenoid(self.serial_no)
            self.device.Connect(self.serial_no)
            
            # Ensure that the device settings have been initialized
            if not self.device.IsSettingsInitialized():
                self.device.WaitForSettingsInitialized(10000)  # 10 second timeout
                assert self.device.IsSettingsInitialized() is True
            
            self.device.StartPolling(250)  # 250ms polling rate
            time.sleep(0.25)
            self.device.EnableDevice()
            time.sleep(0.5)  # Attendre que le dispositif soit activé
            
            # Get Device Information and display description
            device_info = self.device.GetDeviceInfo()
            print(device_info.Description)

            self.device.SetOperatingMode(SolenoidStatus.OperatingModes.Manual)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize Thorlabs Kinesis API: {e}")
            self.master.destroy()

    def create_widgets(self):
        self.on_off_button = tk.Button(self.master, text="On", command=self.toggle_shutter)
        self.on_off_button.pack(pady=20)

        self.quit_button = tk.Button(self.master, text="Quit", command=self.close_api_and_quit)
        self.quit_button.pack(pady=10)

    def toggle_shutter(self):
        try:
            if self.on_off_button.cget("text") == "On":
                self.device.SetOperatingState(SolenoidStatus.OperatingStates.Active)  # Ouvrir le shutter
                self.on_off_button.config(text="Off")
            else:
                self.device.SetOperatingState(SolenoidStatus.OperatingStates.Inactive)  # Fermer le shutter
                self.on_off_button.config(text="On")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle shutter: {e}")

    def close_api_and_quit(self):
        try:
            if self.device is not None:
                self.device.StopPolling()
                self.device.Disconnect()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to close device connection: {e}")
        finally:
            self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = ShutterControlApp(root)
    root.mainloop()
