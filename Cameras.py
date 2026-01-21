from __future__ import annotations
import PySpin
from dataclasses import dataclass
from Utils import Image

@dataclass
class CameraDescriptor:
    """
    The CameraDescriptor class can hold basic information about a camera.
    """
    VendorName: str
    ModelName: str
    Width: int
    Height: int

class StreamMode:
    """
    **FOR INTERNAL USAGE!**
    Configuration class for operating system dependend data stream between camera and machine.
    """
    TELEDYNE_GIGE_VISION = 0
    """
    Stream mode configuration for modern Windows machines.
    """
    LWF = 1 
    """
    Legacy steam mode configuration for Windows machines
    """
    SOCKET = 2
    """
    Stream mode configuration for Unix-like machines including Darwin (macos) utilizing Unix domain sockets.
    """

class Camera:
    def __init__(self, cam: PySpin.CameraPtr, desc: CameraDescriptor):
        """
        **DO NOT USE!** Constructor for Camera class is only for internal usage. 
        Use Camera.init(...) instead!
        """
        self._cam = cam
        self._desc = desc
    
    @classmethod
    def init(cls, cam: PySpin.CameraPtr, stream_mode: StreamMode) -> Camera:
        """
        Creates and correctly initializes a Camera object. Configures the correct stream mode for the passed in camera handle.
        
        :param cam: Handle to the pysical camera device. You may gain access through the systen instance of Spinnaker.
        :type cam: PySpin.CameraPtr
        :param stream_mode: The correct stream mode based on the operating system should be passed here.
        :type stream_mode: StreamMode
        :return: Initialized Camera object. Still needs manual setup for several device settings.
        :rtype: Camera
        """
        cam.Init()

        match stream_mode:
            case StreamMode.TELEDYNE_GIGE_VISION:
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
        """
        Descriptor property holds general specification data about the pysical camera.
        """
        return self._desc
    
    def setup(self, config = None) -> None:
        """
        Sets up the pysical camera with additional device configuartion such as the image acquisition mode. **WORK IN PROGRESS!**
        
        :param config: Config object (still unspecified).
        :raises PySpin.SpinnakerException: May fail to setup camera correctly.
        """
        try:
            self._cam.TLStream.StreamBufferHandlingMode.SetValue(PySpin.StreamBufferHandlingMode_NewestOnly)
            self._cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)

            self._cam.AcquisitionFrameRateEnable.SetValue(True)
            self._cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            self._cam.GainAuto.SetValue(PySpin.GainAuto_Off)
            self._cam.GammaEnable.SetValue(True)

            self._cam.ExposureTime.SetValue(800)
            max_fps = self._cam.AcquisitionFrameRate.GetMax()
            self._cam.AcquisitionFrameRate.SetValue(max_fps)

            self._cam.ChunkModeActive.SetValue(True)
            self._cam.ChunkSelector.SetValue(PySpin.ChunkSelector_FrameID)
            self._cam.ChunkSelector.SetValue(PySpin.ChunkSelector_Timestamp)
            self._cam.ChunkSelector.SetValue(PySpin.ChunkSelector_ExposureTime)
        
        except PySpin.SpinnakerException as ex:
            print(f"Error during camera setup: {ex}")
            raise
    
    def begin(self) -> None:
        """
        Begins the image acquisition for the pysical camera device. Nessessary before acquiring any images.
        
        :raises PySpin.SpinnakerException: May fail to start the image acquisition.
        """
        try:
            self._cam.TimestampReset.Execute()
            self._cam.BeginAcquisition()
        except PySpin.SpinnakerException as ex:
            print(f"Cannot begin image acquisition: {ex}")
            raise

    def acquire(self) -> Image:
        """
        Acquires an image from the pysical camera device and returns it as frame data (2D Array) in BayerBG format.
        In the case of an Exception, try to handle it gracefully and continue acquiring, because a lost frame does not close the acquisition.
        
        :raises PySpin.SpinnakerException: May fail to acquire an image.
        :raises ValueError: Image data might be corrupted.
        """
        try:
            image = self._cam.GetNextImage()
            if image.IsIncomplete():
                raise ValueError("Image is incomplete.")
            
            chunk_data = image.GetChunkData()
            frame_id = chunk_data.GetFrameID()
            timestamp = chunk_data.GetTimestamp()
            exposure_time = chunk_data.GetExposureTime()
            capture_format = image.GetPixelFormatName()
            capture = image.GetNDArray().copy()
            
            image.Release()
            return Image(frame_id, timestamp, exposure_time, capture_format, capture)
        except Exception as ex:
            print(f"Acqisistion Error: {ex}")
            raise

    def end(self) -> None:
        """
        Stops camera from acquiring more images. Nessesary for cleanup.
        
        :raises PySpin.SpinnakerException: May fail to stop the camera. After that the shutdown is fatal.
        """
        try:
            self._cam.EndAcquisition()
        except PySpin.SpinnakerException as ex:
            print(f"Error while ending acquisition: {ex}")
            raise

    def deinit(self):
        """
        Deinitializes the camera handle to the pysical device. Nessesary for cleanup. 
        """
        self._cam.DeInit()
        del self._cam