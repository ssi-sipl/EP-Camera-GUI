# ===== Day Camera GUI (Standalone) =====
# Requires: Python 3.x, tkinter, pillow, opencv-python, gstreamer
# Save as day_camera_gui.py and run.

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
from gi.repository import Gst
import tkinter as tk
from tkinter import ttk
import numpy as np
import cv2
import time
import threading

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

Gst.init(None)


class DayCameraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Day Camera GUI")
        self.root.geometry("800x600")

        # --- State ---
        self.day_pipeline = None
        self.day_sink = None
        self.day_streaming = False
        self.day_colour_running = False
        self.day_imgtk = None

        # --- Layout ---
        self.video_frame = tk.Frame(self.root, bg="black")
        self.video_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.video_label = tk.Label(self.video_frame, bg="black")
        self.video_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- Controls ---
        controls = ttk.Frame(self.root, padding=6)
        controls.pack(fill="x")
        ttk.Button(controls, text="Start B/W", command=self.start_bw).pack(side="left", padx=6)
        ttk.Button(controls, text="Start Color", command=self.start_color).pack(side="left", padx=6)
        ttk.Button(controls, text="Stop", command=self.stop_stream).pack(side="left", padx=6)

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self.status_var).pack(side="bottom", pady=4)

        # Close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------- Pipeline helpers ----------------
    def _setup_pipeline(self, pipeline_str):
        if self.day_pipeline:
            try:
                self.day_pipeline.set_state(Gst.State.NULL)
            except Exception:
                pass
        self.day_pipeline = Gst.parse_launch(pipeline_str)
        self.day_sink = self.day_pipeline.get_by_name("sink")
        self.day_sink.set_property("emit-signals", True)
        self.day_sink.set_property("max-buffers", 1)
        self.day_sink.set_property("drop", True)
        self.day_sink.connect("new-sample", self._on_sample)

    def _run_pipeline_loop(self, pipeline_str):
        self.stop_stream()  # just in case
        self.day_streaming = True
        self.day_imgtk = None

        try:
            self.day_pipeline = Gst.parse_launch(pipeline_str)
            self.day_sink = self.day_pipeline.get_by_name("sink")
            self.day_sink.set_property("emit-signals", False)
            self.day_sink.set_property("max-buffers", 1)
            self.day_sink.set_property("drop", True)
            self.day_pipeline.set_state(Gst.State.PLAYING)
        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Pipeline error: {e}"))
            return

        # Loop pulling frames
        def pull_frames():
            while self.day_streaming and self.day_pipeline:
                sample = self.day_sink.emit("try-pull-sample", 0)  # non-blocking
                if sample:
                    buf = sample.get_buffer()
                    caps = sample.get_caps()
                    try:
                        w = caps.get_structure(0).get_value("width")
                        h = caps.get_structure(0).get_value("height")
                    except:
                        w, h = 640, 480

                    data = buf.extract_dup(0, buf.get_size())
                    arr = np.frombuffer(data, np.uint8)

                    if arr.size == (h * w):  # grayscale
                        arr = arr.reshape((h, w))
                        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
                    else:
                        arr = arr.reshape((h, w, 3))

                    rgb = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                    rgb = cv2.resize(rgb, (self.video_frame.winfo_width() or 640,
                                        self.video_frame.winfo_height() or 480))
                    img = Image.fromarray(cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB))

                    # Update GUI safely
                    self.root.after(0, lambda img=img: self._update_image(img))

                time.sleep(0.01)

        threading.Thread(target=pull_frames, daemon=True).start()

    def _update_image(self, img):
        if self.day_imgtk is None:
            self.day_imgtk = ImageTk.PhotoImage(img)
            self.video_label.config(image=self.day_imgtk, text="")
        else:
            try:
                self.day_imgtk.paste(img)
            except Exception:
                self.day_imgtk = ImageTk.PhotoImage(img)
                self.video_label.config(image=self.day_imgtk, text="")



    # ---------------- Controls ----------------
    def start_bw(self):
        self._set_status("Starting B/W stream...")
        pipeline = (
            "aravissrc ! "
            "video/x-raw,format=GRAY8,width=1280,height=720,framerate=30/1 ! "
            "videoconvert ! "
            "appsink name=sink"
        )
        threading.Thread(target=lambda: self._run_pipeline_loop(pipeline), daemon=True).start()


    def start_color(self):
        self._set_status("Starting Color stream...")
        pipeline = (
            "aravissrc ! "
            "video/x-raw,format=RGB,width=1280,height=720,framerate=30/1 ! "
            "videoconvert ! "
            "appsink name=sink"
        )
        threading.Thread(target=lambda: self._run_pipeline_loop(pipeline), daemon=True).start()


    def stop_stream(self):
        """Stop day camera stream without blocking the UI"""
        if not self.day_streaming and not self.day_colour_running:
            self._set_status("Stream not running.")
            return

        # Step 1: Update flags and UI immediately
        self.day_streaming = False
        self.day_colour_running = False
        self.day_imgtk = None  # <--- RESET PhotoImage here!
        if PIL_AVAILABLE:
            self.video_label.config(image="", text="Stopped", fg="white", bg="black")
        self._set_status("Stopping stream...")

        # Step 2: Stop pipeline in a background thread
        def worker():
            if self.day_pipeline:
                try:
                    self.day_pipeline.set_state(Gst.State.NULL)
                except Exception:
                    pass
                self.day_pipeline = None
                self.day_sink = None
            self.root.after(0, lambda: self._set_status("Stream stopped."))

        threading.Thread(target=worker, daemon=True).start()


    def _set_status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()

    def on_close(self):
        self.stop_stream()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = DayCameraGUI(root)
    root.mainloop()
