import sys
from Context import Context
from Processor import Processor

# import cv2 as cv

def main() -> int:
    context = Context.Create()
    cameras = context.GetCameras()
   
    processor = Processor.Init(cameras[0])
   
    context.Release()
    return 0

if __name__ == "__main__":
    sys.exit(main())