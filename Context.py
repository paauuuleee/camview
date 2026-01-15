import PySpin
from __future__ import annotations
import platform
from Camera import Camera

class StreamMode:
    TELEDYN_GIGE_VISION = 0
    LWF = 1
    SOCKET = 2

class Context:
    def __init__(self, system: PySpin.SystemPtr, version: PySpin.LibraryVersion, stream_mode: StreamMode):
        self._system = system
        self._version = version
        self._stream_mode = stream_mode

    @classmethod
    def Create(cls) -> Context:
        system = PySpin.SystemPtr(PySpin.System.GetInstance())
        version = PySpin.LibraryVersion(system.GetLibraryVersion())
        
        stream_mode = StreamMode.TELEDYN_GIGE_VISION
        os = platform.system()
        if os == "Linux" or os == "Darwin":
            stream_mode = StreamMode.SOCKET
        
        return cls(system, version, stream_mode)
    
    def Release(self) -> None:
        for cam in self._cameras: cam.DeInit() 
        self._cam_list.Clear()
        self._system.ReleaseInstance()

    def GetCameras(self) -> list[Camera]:
        self._cam_list = PySpin.CameraList(self._system.GetCameras())
        self._cameras = [Camera.Init(cam, self._stream_mode) for cam in self._cam_list] 
        return self._cameras