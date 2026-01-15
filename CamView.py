import sys
from Contexts import Context

def main() -> int:
    context = Context.Create()
    try:
        cameras = context.GetCameras()
        cameras[0].Display()
    except Exception as ex:
        print(f"Error: {ex}") 
        return 1 
    
    context.Release()
    return 0

if __name__ == "__main__":
    sys.exit(main())