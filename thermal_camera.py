import cv2, time, threading, serial
from PIL import Image, ImageTk
from utils import overlay_crosshair, build_sumcheck, checksum_response

class ThermalCamera:
    def __init__(self, gui_ref):
        self.gui = gui_ref
        self.cap = None
        self.streaming = False
        self.palette = "white"
        self.ser = None
        self.connected = False

    # ================= UART =================
    def connect_uart(self, port, baud=115200):
        try:
            self.ser = serial.Serial(port, baudrate=baud, timeout=1)
            self.connected = True
            self.gui._set_status(f"Thermal UART connected: {port}")
        except Exception as e:
            self.gui._set_status(f"UART connect error: {e}")

    def disconnect_uart(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.connected = False
            self.gui._set_status("Thermal UART disconnected.")
        except Exception as e:
            self.gui._set_status(f"UART disconnect error: {e}")

    # ================= Stream =================
    def start_stream(self, index=0):
        if self.streaming:
            self.gui._set_status("Thermal already streaming")
            return
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            self.gui._set_status("Cannot open thermal cam")
            return
        self.streaming = True
        self._tick()

    def _tick(self):
        if not (self.streaming and self.cap):
            return
        ok, frame = self.cap.read()
        if ok:
            show = self._apply_palette(frame)
            if self.gui.crosshair_enabled:
                show = overlay_crosshair(show)
            rgb = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.gui.thermal_video_label.imgtk = imgtk
            self.gui.thermal_video_label.config(image=imgtk)
        self.gui.root.after(30, self._tick)

    def _apply_palette(self, frame):
        try:
            if self.palette == "white":
                return cv2.applyColorMap(frame, cv2.COLORMAP_BONE)
            elif self.palette == "black":
                return cv2.applyColorMap(frame, cv2.COLORMAP_OCEAN)
            elif self.palette == "rainbow":
                return cv2.applyColorMap(frame, cv2.COLORMAP_JET)
            elif self.palette == "green":
                return cv2.applyColorMap(frame, cv2.COLORMAP_SUMMER)
            elif self.palette == "metel":
                return cv2.applyColorMap(frame, cv2.COLORMAP_HOT)
        except:
            pass
        return frame

    def stop(self):
        self.streaming = False
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.gui.thermal_video_label.config(image="", text="", bg="black")
        except:
            pass
        self.gui._set_status("Thermal stopped.")
