import sys
from Contexts import Context
from Processors import Processor, PixelFormat, ProcessFilter
from Dispatchers import Viewer

def main() -> int:
    context = Context.create()

    try:
        cameras = context.get_cameras()
    except Exception as ex:
        print(f"CamView Error: {ex}")
        return 1
    
    processor = Processor.create(PixelFormat.BGR, ProcessFilter.MEDIAN(3))
    viewer = Viewer.create(cameras[0], processor)
    viewer.consumer_loop()
    
    context.release()
    return 0

if __name__ == "__main__":
    sys.exit(main())