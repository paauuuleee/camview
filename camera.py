from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from utils import FrameData, Frame, except_continue, except_raise

import PySpin

@dataclass
class CameraConfig:
    width: int | None = None
    height: int | None = None
    offset_x: int | None = None
    offset_y: int | None = None
    frame_rate: int | None = None
    adc_bit_depth: Any | None = None
    exposure_time: int | None = None
    gain: float | None = None
    gamma: float | None = None

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
    def __init__(self, name: str, cam: PySpin.CameraPtr):
        """
        **DO NOT USE!** Constructor for Camera class is only for internal usage. 
        Use Camera.init(...) instead!
        """
        self._name = name
        self._cam = cam
        self._config: CameraConfig
    
    @classmethod
    def init(cls, name: str, cam: PySpin.CameraPtr, stream_mode: StreamMode) -> Camera:
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

        return cls(name, cam)

    def setup(self) -> None:
        """
        Sets up the pysical camera with additional device configuartion such as the image acquisition mode. **WORK IN PROGRESS!**
        
        :param config: Config object (still unspecified).
        :raises PySpin.SpinnakerException: May fail to setup camera correctly.
        """
        with except_raise("Error during camera setup"):
            self._cam.TLStream.StreamBufferHandlingMode.SetValue(PySpin.StreamBufferHandlingMode_NewestOnly)
            self._cam.TLStream.StreamBufferCountMode.SetValue(PySpin.StreamBufferCountMode_Manual)
            self._cam.TLStream.StreamBufferCountManual.SetValue(3)
            self._cam.GevSCPSPacketSize.SetValue(9000)
            self._cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)

            self._cam.ChunkModeActive.SetValue(True)
            self._cam.ChunkSelector.SetValue(PySpin.ChunkSelector_FrameID)
            self._cam.ChunkSelector.SetValue(PySpin.ChunkSelector_Timestamp)
            self._cam.ChunkSelector.SetValue(PySpin.ChunkSelector_ExposureTime)

            self._cam.AcquisitionFrameRateEnable.SetValue(True)
            self._cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            self._cam.GainAuto.SetValue(PySpin.GainAuto_Off)
            self._cam.GammaEnable.SetValue(True)
            if self._cam.BalanceWhiteAuto.GetAccessMode() == PySpin.RW:
                self._cam.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Off)

        self.update_config()
        
    def update_config(self) -> None:
        self._config = CameraConfig(
            width = self._cam.Width.GetValue(),
            height = self._cam.Height.GetValue(),
            offset_x = self._cam.OffsetX.GetValue(),
            offset_y = self._cam.OffsetY.GetValue(),
            frame_rate = self._cam.AcquisitionFrameRate.GetValue(),
            adc_bit_depth = self._cam.AdcBitDepth.GetValue(),
            exposure_time = self._cam.ExposureTime.GetValue(),
            gain = self._cam.Gain.GetValue(),
            gamma = self._cam.Gamma.GetValue()
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def config(self) -> CameraConfig:
        return self._config

    @config.setter
    def config(self, config: CameraConfig) -> None:
        if not self._cam.IsStreaming():
            if config.height is not None:
                with except_continue():
                    self._cam.Width.SetValue(config.width)
            
            if config.width is not None:
                with except_continue():
                    self._cam.Height.SetValue(config.height)
            
            if config.adc_bit_depth is not None:
                with except_continue():
                    self._cam.AdcBitDepth.SetValue(config.adc_bit_depth)

        if config.offset_x is not None:
            with except_continue():
                self._cam.OffsetX.SetValue(config.offset_x)

        if config.offset_y is not None:
            with except_continue():
                self._cam.OffsetY.SetValue(config.offset_y)

        if config.exposure_time is not None:
            with except_continue():
                self._cam.ExposureTime.SetValue(config.exposure_time)

        if config.gain is not None:
            with except_continue():
                self._cam.Gain.SetValue(config.gain)

        if config.gamma is not None:
            with except_continue():
                self._cam.Gamma.SetValue(config.gamma)
        
        if config.frame_rate is not None:
            frame_rate = self._cam.AcquisitionFrameRate.GetMax()
            if config.frame_rate < frame_rate: 
                frame_rate = config.frame_rate
            with except_continue():
                self._cam.AcquisitionFrameRate.SetValue(frame_rate)

        self.update_config()
            
    def begin(self) -> None:
        """
        Begins the image acquisition for the pysical camera device. Nessessary before acquiring any images.
        
        :raises PySpin.SpinnakerException: May fail to start the image acquisition.
        """
        with except_raise("Cannot begin image acquisition"):
            self._cam.TimestampReset.Execute()
            self._cam.BeginAcquisition()

    def acquire(self) -> tuple[FrameData, Frame]:
        """
        Acquires an image from the pysical camera device and returns it as frame data (2D Array) in BayerBG format.
        In the case of an Exception, try to handle it gracefully and continue acquiring, because a lost frame does not close the acquisition.
        
        :raises PySpin.SpinnakerException: May fail to acquire an image.
        :raises ValueError: Image data might be corrupted.
        """
        with except_raise("Acquisition error"):
            image = self._cam.GetNextImage()
            if image.IsIncomplete():
                raise ValueError("Image is incomplete.")
            
            chunk_data = image.GetChunkData()
            frame_id = chunk_data.GetFrameID()
            timestamp = chunk_data.GetTimestamp()
            exposure_time = chunk_data.GetExposureTime()
            capture_format = image.GetPixelFormatName()
            frame = image.GetNDArray().copy()
            
            image.Release()
            return FrameData(frame_id, timestamp, exposure_time, capture_format), frame

    def end(self) -> None:
        """
        Stops camera from acquiring more images. Nessesary for cleanup.
        
        :raises PySpin.SpinnakerException: May fail to stop the camera. After that the shutdown is fatal.
        """
        with except_raise("Error while ending acquisition"):
            self._cam.EndAcquisition()

    def deinit(self):
        """
        Deinitializes the camera handle to the pysical device. Nessesary for cleanup. 
        """
        self._cam.DeInit()
        del self._cam