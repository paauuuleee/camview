import sys
from Contexts import Context
from Processors import Processor, PixelFormat
from Dispatchers import Viewer

def main() -> int:
    context = Context.create()

    try:
        cameras = context.get_cameras()
    except Exception as ex:
        print(f"CamView Error: {ex}")
        return 1
    
    processor = Processor.create(PixelFormat.BGR)
    viewer = Viewer.create(cameras[0], processor)
    viewer.consumer_loop()
    
    context.release()
    return 0

if __name__ == "__main__":
    sys.exit(main())