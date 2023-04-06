import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from wand.image import Image

MM_TO_INCHES = 0.03937007874

def get_dpi(filename,frame_width,frame_height=None):
    with Image(filename=filename) as img:
        w, h = img.size
        return w / frame_width
    # TODO: check vertical DPI as well if provided

def main(args):
    filename = args[0]
    frame_width = args[1] ## in MM
    dpi = get_dpi(filename, frame_width * MM_TO_INCHES)
    print(f"{Path(filename).name}: {round(dpi,1)} DPI")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv[1:])
    else:
        print("Missing arguments: filename frame_width [frame_height]")
