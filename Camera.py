import PySpin
from Camera import StreamMode
import queue
import threading
from __future__ import annotations

class Camera:
    def __init__(self, cam: PySpin.CameraPtr):
        self._cam = cam
    
    @classmethod
    def Init(cls, cam: PySpin.CameraPtr, stream_mode: StreamMode) -> Camera:
        cam.Init()
        
        match stream_mode:
            case StreamMode.TELEDYN_GIGE_VISION:
                cam.TLStream.StreamMode.SetValue(PySpin.StreamMode_TeledyneGigeVision)
            case StreamMode.LWF:
                cam.TLStream.StreamMode.SetValue(PySpin.StreamMode_LWF)
            case StreamMode.SOCKET:
                cam.TLStream.StreamMode.SetValue(PySpin.StreamMode_Socket)

        return cls(cam)
    
    def Setup(self, pixel_format) -> None:
        self._cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        self._cam.PixelFormat.SetValue(pixel_format)
    
    def Acquire(self, data_channel: queue.Queue, stop_signal: threading.Event) -> None:
        try:
            self._cam.BeginAcquisition()

            while not stop_signal.is_set():
                try:
                    image = PySpin.ImagePtr(self._cam.GetNextImage())
                    if not image.IsIncomplete():
                        data = image.GetNDArray().copy()

                        try:
                            data_channel.put(data, block=False)
                        except queue.Full:
                            pass
                except PySpin.SpinnakerException as ex:
                    print(f"Error: {ex}")
                    break
                
            self._cam.EndAcquisition()
        except PySpin.SpinnakerException as ex:
            print(f"Error: {ex}")
            raise

    def DeInit(self):
        self._cam.DeInit()
        del self._cam