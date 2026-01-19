from __future__ import annotations
from Utils import Frame
from typing import TypeAlias, Callable
import cv2 as cv

class PixelFormat:
    """
    Configuration class for the resulting pixel format after processing the frame.
    """
    RGB = 0
    """
    Pixel format of (red - uint8, green - uint8, blue - uint8)
    """
    BGR = 1
    """
    Pixel format of (blue - uint8, green - uint8, red - uint8)
    """

FrameFilter: TypeAlias = Callable[[Frame], Frame]
"""
Type alias for a filter function that processes the frame data.
"""

class ProcessFilter:
    """
    Enumeration over already available filter functions.
    """
    @staticmethod
    def MEDIAN(ksize: int) -> FrameFilter:
        """
        Returns a FrameFilter function objet that applys a median filter with specified kernal size.
        
        :param ksize: Kernal size for the median filter.
        :type: int
        :return: Returns the FrameFilter function object.
        :rtype: FrameFilter
        """
        return lambda frame: cv.medianBlur(frame, ksize)
    
    def SUBSTRACT(sub: Frame) -> FrameFilter:
        return lambda frame: cv.subtract(frame, sub)
        

class Processor:
    def __init__(self, filters: tuple[FrameFilter, ...]):
        """
        **DO NOT USE!** Constructor for Processor class is only for internal usage.
        Use Processor.create(...) instead
        """
        self._filters = filters

    @classmethod
    def create(cls, *filters: FrameFilter) -> Processor:
        """
        Takes a variadic amount of FrameFilter function objects to be subsequently applied onto a provided image frame.
        
        :param filters: Pass as many FrameFilter functions as you like.
        :type filters: FrameFilter
        :return: Processor object with initialized filter pipeline.
        :rtype: Processor
        """
        return cls(filters)
    
    def setup(self, pixel_format: PixelFormat) -> None:
        """
        Setup the desired pixel format that the resulting frame should be converted to.
        
        :param pixel_format: Final pixel format of the processed frame.
        :type pixel_format: PixelFormat
        """
        self._conversion_code = self._get_conversion_code(pixel_format)
    
    @staticmethod
    def _get_conversion_code(pixel_format: PixelFormat) -> int:
        """
        Determines the conversion code for OpenCV library to convert the BayerBG8 frame data to desired pixel format. Only for internal usage.
        """
        match pixel_format:
            case PixelFormat.RGB: return cv.COLOR_BayerBG2RGB
            case PixelFormat.BGR: return cv.COLOR_BayerBG2BGR

    def process(self, bayer_frame: Frame) -> Frame:
        """
        First converts the passed in image frame of the camera and converts it from BayerBG8 to the desired pixel format and then applies all specified FrameFilters before it returns the result.
        
        :param bayer_frame: Pass the acquired image frame from the camera in here.
        :type bayer_frame: Frame
        :return: Processed frame data with correct pixel format and all FrameFilters applied. 
        :rtype: Frame
        """
        frame = cv.cvtColor(bayer_frame, self._conversion_code)
        for filter in self._filters:
            frame = filter(frame)
        return frame