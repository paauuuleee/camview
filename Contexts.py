from __future__ import annotations
import PySpin
import platform
from Cameras import Camera, StreamMode

class Context:
    """
    The Context class gives access to connected cameras.
    """
    
    def __init__(self, system: PySpin.SystemPtr, stream_mode: StreamMode, cameras: PySpin.CameraList):
        """
        **DO NOT USE!** Constructor for Context class is only for internal usage. 
        Use Context.create() instead!
        """
        self._system = system
        self._stream_mode = stream_mode
        self._cameras = cameras

    @classmethod
    def create(cls) -> Context:
        """
        Creates a Context object. Context is nessessary to gain access to the connected cameras.
        
        :return: Returns a Context object (Factory function)
        :rtype: Context
        """
        system = PySpin.System.GetInstance()
        
        stream_mode = StreamMode.TELEDYNE_GIGE_VISION
        os = platform.system()
        if os == "Linux" or os == "Darwin":
            stream_mode = StreamMode.SOCKET
        
        return cls(system, stream_mode, system.GetCameras())
    
    def search_cams(self) -> None:
        self._cameras = self._system.GetCameras()
    
    def get_camera(self, id: int) -> Camera:
        if self._cameras.GetSize() == 0:
            raise Exception("No cameras connected!")
        
        cam = self._cameras.RemoveByIndex(0)
        return Camera.init(cam, self._stream_mode)
    
    def release(self) -> None:
        """
        Nessessary for cleanup. Releases the objects the Context class holds a pointer to.
        """
        self._cameras.Clear()
        self._system.ReleaseInstance()