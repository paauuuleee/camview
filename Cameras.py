from __future__ import annotations
import PySpin
from dataclasses import dataclass
from Utils import Frame

@dataclass
class CameraDescriptor:
    VendorName: str
    ModelName: str
    Width: int
    Height: int

class StreamMode:
    TELEDYN_GIGE_VISION = 0
    LWF = 1
    SOCKET = 2

class Camera:
    def __init__(self, cam: PySpin.CameraPtr, desc: CameraDescriptor):
        self._cam = cam
        self._desc = desc
    
    @classmethod
    def init(cls, cam: PySpin.CameraPtr, stream_mode: StreamMode) -> Camera:
        cam.Init()
        
        match stream_mode:
            case StreamMode.TELEDYN_GIGE_VISION:
                cam.TLStream.StreamMode.SetValue(PySpin.StreamMode_TeledyneGigeVision)
            case StreamMode.LWF:
                cam.TLStream.StreamMode.SetValue(PySpin.StreamMode_LWF)
            case StreamMode.SOCKET:
                cam.TLStream.StreamMode.SetValue(PySpin.StreamMode_Socket)

        desc = CameraDescriptor(
            cam.DeviceVendorName.GetValue(), 
            cam.DeviceModelName.GetValue(), 
            cam.Width.GetValue(), 
            cam.Height.GetValue()
        )

        return cls(cam, desc)

    @property
    def descriptor(self) -> CameraDescriptor:
        return self._desc
    
    def begin(self) -> None:
        try:
            self._cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
            self._cam.BeginAcquisition()
        except PySpin.SpinnakerException as ex:
            print(f"Cannot begin image aqcisition: {ex}")
            raise

    def acquire(self) -> Frame:
        try:
            image = self._cam.GetNextImage()
            if image.IsIncomplete():
                raise Exception("Image is incomplete.")
            frame = image.GetNDArray().copy()
            image.Release()
            return frame
        except Exception as ex:
            print(f"Acqisistion Error: {ex}")
            raise

    def end(self) -> None:
        try:
            self._cam.EndAcquisition()
        except PySpin.SpinnakerException as ex:
            print(f"Error while ending acquisition: {ex}")
            raise

    def deinit(self):
        self._cam.DeInit()
        del self._cam