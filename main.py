import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
from gi.repository import Gst
import numpy as np
import cv2
import serial
import serial.tools.list_ports
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import os

from PIL import Image, ImageTk

# === Import modules ===
from day_camera import DayCamera
from thermal_camera import ThermalCamera
from lrf import LRF
from utils import overlay_crosshair

Gst.init(None)


class TriplePayloadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Entangled Photons EO/IR")
        self.root.geometry("1500x900")

        # --- Module instances ---
        self.day = DayCamera(self)
        self.thermal = ThermalCamera(self)
        self.lrf = LRF(self)

        # Crosshair state
        self.crosshair_enabled = False

        # --- Build UI layout ---
        self._build_layout()

        # Bind close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ===================== UI LAYOUT =====================
    def _build_layout(self):
        # -------- Header --------
        self.header = ttk.Frame(self.root, padding=(8, 6))
        self.header.pack(fill="x")

        self.title_label = ttk.Label(
            self.header,
            text="Entangled Photons EO/IR",
            font=("Segoe UI", 40, "bold"),
        )
        self.title_label.pack(expand=True, anchor="center")

        # -------- Main body --------
        self.body = ttk.Frame(self.root, padding=6)
        self.body.pack(fill="both", expand=True)
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_columnconfigure(1, weight=1)
        self.body.grid_columnconfigure(2, weight=0)

        # ---- Day stream ----
        self.s1_group = ttk.Labelframe(self.body, text="STREAM-01 (Day Camera)")
        self.s1_group.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.s1_group.grid_rowconfigure(0, weight=1)
        self.s1_group.grid_columnconfigure(0, weight=1)

        self.day_video_frame = tk.Frame(self.s1_group, bg="black")
        self.day_video_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.day_video_label = tk.Label(self.day_video_frame, bg="black")
        self.day_video_label.place(relx=0.5, rely=0.5, anchor="center")

        # ---- Thermal stream ----
        self.s2_group = ttk.Labelframe(self.body, text="STREAM-02 (Thermal Camera)")
        self.s2_group.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self.s2_group.grid_rowconfigure(0, weight=1)
        self.s2_group.grid_columnconfigure(0, weight=1)

        self.thermal_video_frame = tk.Frame(self.s2_group, bg="black")
        self.thermal_video_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.thermal_video_label = tk.Label(self.thermal_video_frame, bg="black")
        self.thermal_video_label.place(relx=0.5, rely=0.5, anchor="center")

        # LRF overlay
        self.lrf_overlay = tk.Label(self.thermal_video_frame,
                                    text="Range: --.- m",
                                    font=("Segoe UI", 12, "bold"),
                                    fg="cyan", bg="black")
        self.lrf_overlay.place(relx=1.0, rely=0.0, anchor="ne", x=-8, y=8)

        # -------- Controls --------
        self.controls = ttk.Frame(self.root, padding=6)
        self.controls.pack(fill="x")

        # Day controls
        day_ctrl = ttk.Frame(self.controls)
        day_ctrl.pack(side="left", padx=6)
        ttk.Label(day_ctrl, text="DAY").pack(side="left", padx=(0,6))
        ttk.Button(day_ctrl, text="Start B/W", command=self.day.start_bw).pack(side="left", padx=4)
        ttk.Button(day_ctrl, text="Start Colour", command=self.day.start_color).pack(side="left", padx=4)
        ttk.Button(day_ctrl, text="Stop", command=self.day.stop).pack(side="left", padx=4)

        # Thermal controls
        th_ctrl = ttk.Frame(self.controls)
        th_ctrl.pack(side="left", padx=12)
        ttk.Label(th_ctrl, text="THERMAL").pack(side="left", padx=(0,6))
        ttk.Button(th_ctrl, text="Start", command=self.thermal.start_stream).pack(side="left", padx=4)
        ttk.Button(th_ctrl, text="Stop", command=self.thermal.stop).pack(side="left", padx=4)

        # LRF controls
        lrf_ctrl = ttk.Frame(self.controls)
        lrf_ctrl.pack(side="left", padx=12)
        ttk.Label(lrf_ctrl, text="LRF").pack(side="left", padx=(0,6))
        ttk.Button(lrf_ctrl, text="Start", command=lambda: self.lrf.start("/dev/ttyUSB0")).pack(side="left", padx=4)
        ttk.Button(lrf_ctrl, text="Stop", command=self.lrf.stop).pack(side="left", padx=4)

        # Crosshair toggle
        ttk.Button(self.controls, text="Toggle Crosshair", command=self.toggle_crosshair).pack(side="left", padx=8)

        # -------- Status bar --------
        self.footer = ttk.Frame(self.root, padding=(8, 4))
        self.footer.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self.footer, textvariable=self.status_var).pack(side="left")

    # ===================== Helpers =====================
    def _set_status(self, msg):
        self.status_var.set(msg)
        print(msg)

    def toggle_crosshair(self):
        self.crosshair_enabled = not self.crosshair_enabled
        self._set_status("Crosshair " + ("enabled" if self.crosshair_enabled else "disabled"))

    # ===================== Cleanup =====================
    def on_close(self):
        self.day.stop()
        self.thermal.stop()
        self.lrf.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TriplePayloadGUI(root)
    root.mainloop()
