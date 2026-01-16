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
    def create(cls) -> Context:
        system = PySpin.System.GetInstance()
        
        stream_mode = StreamMode.TELEDYN_GIGE_VISION
        os = platform.system()
        if os == "Linux" or os == "Darwin":
            stream_mode = StreamMode.SOCKET
        
        return cls(system, stream_mode)
    
    def release(self) -> None:
        for cam in self._cameras: cam.deinit() 
        self._cam_list.Clear()
        self._system.ReleaseInstance()

    def get_cameras(self) -> list[Camera]:
        self._cam_list = self._system.GetCameras()

        if self._cam_list.GetSize() == 0:
            self.release()
            raise Exception("No cameras connected.")

        self._cameras = [Camera.init(cam, self._stream_mode) for cam in self._cam_list] 
        return self._cameras