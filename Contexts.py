from __future__ import annotations
import PySpin
import platform
from Cameras import Camera, StreamMode

class Context:
    def __init__(self, system: PySpin.SystemPtr, stream_mode: StreamMode):
        self._system = system
        self._stream_mode = stream_mode
        self._cameras: list[Camera] = []

    @classmethod
    def Create(cls) -> Context:
        system = PySpin.System.GetInstance()
        
        stream_mode = StreamMode.TELEDYN_GIGE_VISION
        os = platform.system()
        if os == "Linux" or os == "Darwin":
            stream_mode = StreamMode.SOCKET
        
        return cls(system, stream_mode)
    
    def Release(self) -> None:
        for cam in self._cameras: cam.DeInit() 
        self._cam_list.Clear()
        self._system.ReleaseInstance()

    def GetCameras(self) -> list[Camera]:
        self._cam_list = self._system.GetCameras()

        if self._cam_list.GetSize() == 0:
            self.Release()
            raise Exception("No cameras connected.")

        self._cameras = [Camera.Init(cam, self._stream_mode) for cam in self._cam_list] 
        return self._cameras