import serial, threading, time

STOP_MEASUREMENT        = bytes([0x55, 0xAA, 0x8E, 0xFF, 0xFF, 0xFF, 0xFF, 0x8A])
CONTINUOUS_MEASUREMENT  = bytes([0x55, 0xAA, 0x89, 0xFF, 0xFF, 0xFF, 0xFF, 0x85])

class LRF:
    def __init__(self, gui_ref):
        self.gui = gui_ref
        self.ser = None
        self.running = False
        self.thread = None
        self.last_distance = None

    def start(self, port, baud=115200):
        try:
            self.ser = serial.Serial(port, baudrate=baud, timeout=1)
            self.ser.write(CONTINUOUS_MEASUREMENT)
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            self.gui._set_status("LRF started.")
        except Exception as e:
            self.gui._set_status(f"LRF start error: {e}")

    def stop(self):
        self.running = False
        try:
            if self.ser and self.ser.is_open:
                self.ser.write(STOP_MEASUREMENT)
                self.ser.close()
            self.gui._set_status("LRF stopped.")
        except Exception as e:
            self.gui._set_status(f"LRF stop error: {e}")

    def _read_loop(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting >= 8:
                    data = self.ser.read(8)
                    if len(data) == 8 and data[4] != 0x00:
                        self.last_distance = (data[5] * 256 + data[6]) / 10.0
                        self.gui.root.after(0, self._update_gui)
                else:
                    time.sleep(0.05)
            except:
                time.sleep(0.1)

    def _update_gui(self):
        if self.last_distance:
            txt = f"Range: {self.last_distance:.1f} m"
        else:
            txt = "Range: --.- m"
        self.gui.lrf_overlay.config(text=txt)
