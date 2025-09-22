import tkinter as tk
from tkinter import ttk
from day_camera import DayCamera
from thermal_camera import ThermalCamera
from lrf import LRF

class TriplePayloadGUI:
    def __init__(self, root):
        self.root = root
        self.crosshair_enabled = False

        # Create modules
        self.day = DayCamera(self)
        self.thermal = ThermalCamera(self)
        self.lrf = LRF(self)

        # Build UI
        self._build_layout()

    def _build_layout(self):
        self.day_video_label = tk.Label(self.root, bg="black")
        self.day_video_label.pack(side="left", expand=True, fill="both")
        self.thermal_video_label = tk.Label(self.root, bg="black")
        self.thermal_video_label.pack(side="left", expand=True, fill="both")
        self.lrf_overlay = tk.Label(self.root, text="Range: --.- m", fg="cyan", bg="black")
        self.lrf_overlay.pack(side="bottom", fill="x")

        ctrl = ttk.Frame(self.root)
        ctrl.pack(side="bottom", fill="x")
        ttk.Button(ctrl, text="Day Start", command=self.day.start_bw).pack(side="left")
        ttk.Button(ctrl, text="Day Stop", command=self.day.stop).pack(side="left")
        ttk.Button(ctrl, text="Thermal Start", command=self.thermal.start_stream).pack(side="left")
        ttk.Button(ctrl, text="Thermal Stop", command=self.thermal.stop).pack(side="left")
        ttk.Button(ctrl, text="Toggle Crosshair", command=self.toggle_crosshair).pack(side="left")

    def toggle_crosshair(self):
        self.crosshair_enabled = not self.crosshair_enabled
        self._set_status("Crosshair ON" if self.crosshair_enabled else "Crosshair OFF")

    def _set_status(self, msg):
        print(msg)

    def on_close(self):
        self.day.stop()
        self.thermal.stop()
        self.lrf.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TriplePayloadGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
