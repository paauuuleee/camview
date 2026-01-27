from __future__ import annotations

from camera import Camera, StreamMode

import PySpin
import platform
import json

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
        self._cameras: PySpin.CameraList
        self._cam_map: dict[str, str] 
        self._connected: dict[str, str] 
        self.search_cams(True)

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
        
        return cls(system, stream_mode)
    
    def get_connected(self) -> list[str]:
        return self._connected.keys()
    
    def search_cams(self, read_config: bool) -> list[str]:
        if read_config:
            with open("./config/camera_map.json", "r") as file:
                self._cam_map = json.load(file)

        self._cameras = self._system.GetCameras()
        
        self._connected = {
            cam_key: cam_serial 
            for cam_key, cam_serial in self._cam_map.items() 
            if self._cameras.GetBySerial(cam_serial).IsValid()
        }
    
    def get_camera(self, name: str) -> Camera:
        if not name in self._connected:
            raise Exception("This camera is not connected!")
        
        cam = self._cameras.GetBySerial(self._cam_map[name])
        return Camera.init(name, cam, self._stream_mode)
    
    def release(self) -> None:
        """
        Nessessary for cleanup. Releases the objects the Context class holds a pointer to.
        """
        self._cameras.Clear()
        self._system.ReleaseInstance()