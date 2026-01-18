from __future__ import annotations
import PySpin
import platform
from Cameras import Camera, StreamMode

class Context:
    """
    The Context class gives access to connected cameras.
    """
    
    def __init__(self, system: PySpin.SystemPtr, stream_mode: StreamMode):
        """
        **DO NOT USE!** Constructor for Context class is only for internal usage. 
        Use Context.create() instead!
        """
        self._system = system
        self._stream_mode = stream_mode
        self._cameras: list[Camera] = []

    @classmethod
    def create(cls) -> Context:
        """
        Creates a Context object. Context is nessessary to gain access to the connected cameras.
        
        :return: Returns a Context object (Factory function)
        :rtype: Context
        """
        system = PySpin.System.GetInstance()
        
        stream_mode = StreamMode.TELEDYN_GIGE_VISION
        os = platform.system()
        if os == "Linux" or os == "Darwin":
            stream_mode = StreamMode.SOCKET
        
        return cls(system, stream_mode)
    
    def release(self) -> None:
        """
        Nessessary for cleanup. Releases the objects the Context class holds a pointer to.
        """
        for cam in self._cameras: cam.deinit() 
        self._cam_list.Clear()
        self._system.ReleaseInstance()

    def get_cameras(self) -> list[Camera]:
        """
        Gain access to the connected cameras through return list of Camera objects.
        
        :return: Camera object for all connected cameras.
        :rtype: list[Camera]
        :raises RuntimeError: If no cameras are connected. 
        Context object is already properly released and does not requiere additional cleanup.
        """
        self._cam_list = self._system.GetCameras()

        if self._cam_list.GetSize() == 0:
            self.release()
            raise RuntimeError("No cameras connected.")

        self._cameras = [Camera.init(cam, self._stream_mode) for cam in self._cam_list] 
        return self._cameras