from __future__ import annotations
import PySpin
from dataclasses import dataclass
import cv2 as cv
from Utils import Timer

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
    def Init(cls, cam: PySpin.CameraPtr, stream_mode: StreamMode) -> Camera:
        cam.Init()
        
        match stream_mode:
            case StreamMode.TELEDYN_GIGE_VISION:
                cam.TLStream.StreamMode.SetValue(PySpin.StreamMode_TeledyneGigeVision)
            case StreamMode.LWF:
                cam.TLStream.StreamMode.SetValue(PySpin.StreamMode_LWF)
            case StreamMode.SOCKET:
                cam.TLStream.StreamMode.SetValue(PySpin.StreamMode_Socket)
        
        vendor_name = cam.DeviceVendorName.GetValue()
        model_name = cam.DeviceModelName.GetValue()
        width = cam.Width.GetValue()
        height = cam.Height.GetValue()
        desc = CameraDescriptor(vendor_name, model_name, width, height)

        return cls(cam, desc)

    @property
    def Descriptor(self) -> CameraDescriptor:
        return self._desc
    
    def Setup(self) -> None:
        try:
            self._cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        except PySpin.SpinnakerException as ex:
            print(f"Error: {ex}")
            raise
    
    def Display(self) -> None:
        self.Setup()

        try:
            self._cam.BeginAcquisition()
            cv.namedWindow("camview", cv.WINDOW_AUTOSIZE)

            timer = Timer.Create(100, lambda fps: print(f"Frame rate: {fps:.1f}"))
            timer.Start()

            while True:
                raw_frame = self.Acquire()
                frame = self.Process(raw_frame)
                cv.imshow("camview", frame)

                timer.Frame()
            
                if cv.waitKey(1) & 0xFF == ord(' '):
                    break
            
            self._cam.EndAcquisition()
        except PySpin.SpinnakerException as ex:
            print(f"Error: {ex}")
            raise

    def Process(self, bayer_frame: cv.typing.MatLike) -> cv.typing.MatLike:
        return cv.cvtColor(bayer_frame, cv.COLOR_BayerBG2BGR)

    def Acquire(self) -> cv.typing.MatLike:
        try:
            image = self._cam.GetNextImage()
            if not image.IsIncomplete():
                return image.GetNDArray().copy()
        except PySpin.SpinnakerException as ex:
            print(f"Error: {ex}")
            raise

    def DeInit(self):
        self._cam.DeInit()
        del self._cam