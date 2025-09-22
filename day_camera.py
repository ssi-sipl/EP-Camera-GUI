import gi, cv2, numpy as np, time
from gi.repository import Gst
from PIL import Image, ImageTk
from utils import overlay_crosshair

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
Gst.init(None)


class DayCamera:
    def __init__(self, gui_ref):
        self.gui = gui_ref
        self.pipeline = None
        self.sink = None
        self.streaming = False
        self.colour_running = False

    def _setup_pipeline(self, pipeline_str):
        if self.pipeline:
            try:
                self.pipeline.set_state(Gst.State.NULL)
            except:
                pass
        self.pipeline = Gst.parse_launch(pipeline_str)
        self.sink = self.pipeline.get_by_name("sink")
        self.sink.set_property("emit-signals", True)
        self.sink.set_property("max-buffers", 1)
        self.sink.set_property("drop", True)
        self.sink.connect("new-sample", self._on_sample)

    def _on_sample(self, sink):
        sample = sink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.OK
        buf = sample.get_buffer()
        caps = sample.get_caps()
        w, h = caps.get_structure(0).get_value("width"), caps.get_structure(0).get_value("height")
        data = buf.extract_dup(0, buf.get_size())
        arr = np.frombuffer(data, np.uint8).reshape((h, w))
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)

        if self.gui.crosshair_enabled:
            arr = overlay_crosshair(arr)

        img = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
        imgtk = ImageTk.PhotoImage(img)
        self.gui.day_video_label.config(image=imgtk)
        self.gui.day_video_label.imgtk = imgtk
        return Gst.FlowReturn.OK

    def start_bw(self):
        if self.streaming:
            self.gui._set_status("Day cam already running")
            return
        pipeline_str = (
            "aravissrc ! video/x-raw,format=GRAY8,width=1920,height=1080,framerate=30/1 ! "
            "videoconvert ! appsink name=sink"
        )
        try:
            self._setup_pipeline(pipeline_str)
            self.pipeline.set_state(Gst.State.PLAYING)
            self.streaming = True
            self.gui._set_status("Day camera (B/W) started.")
        except Exception as e:
            self.gui._set_status(f"Day cam error: {e}")

    def start_color(self):
        if self.streaming:
            self.stop()
        pipeline_str = (
            "aravissrc ! video/x-raw,format=RGB,width=1920,height=1080,framerate=30/1 ! "
            "videoconvert ! appsink name=sink"
        )
        try:
            self._setup_pipeline(pipeline_str)
            self.pipeline.set_state(Gst.State.PLAYING)
            self.streaming = True
            self.colour_running = True
            self.gui._set_status("Day camera (Colour) started.")
        except Exception as e:
            self.gui._set_status(f"Day cam error: {e}")

    def stop(self):
        if not self.streaming:
            return
        self.streaming = False
        self.colour_running = False
        try:
            if self.sink:
                self.sink.disconnect_by_func(self._on_sample)
            if self.pipeline:
                self.pipeline.set_state(Gst.State.NULL)
                self.pipeline = None
                self.sink = None
        except Exception as e:
            self.gui._set_status(f"Day stop error: {e}")
        self.gui._set_status("Day cam stopped.")
