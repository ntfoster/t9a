import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from wand.image import Image

TARGET_DPI = 300
MAX_DPI = 310

TYPES_TO_RESIZE = [".tif",".tiff",".jpg",".jpeg"]
TYPES_TO_COMPRESS = [".tif",".tiff"]

### CONVERSIONS ###

MM_TO_INCHES = 0.03937007874
PTS_TO_INCHES = 0.0138889
PERCENT_TO_LOCAL_SC = 0.24

###################


# logging.basicConfig(level=logging.INFO)

def get_dpi(filename,scale,frame_width,frame_height=None):
    logging.debug(f"Trying to open image: {filename}")
    try:
        with Image(filename=filename) as img:
            w, h = img.size
            logging.debug(f"Image resolution: {w}x{h}")
            original_dpi = img.resolution[0] # only using the x-resolution
            full_width = w / original_dpi * scale
            logging.debug(f"Full size at {original_dpi}: {full_width} in")
            display_area = frame_width/full_width
            local_scale = scale * PERCENT_TO_LOCAL_SC
            display_pixels = display_area * w 
            logging.debug(f"Displayed pixels in {frame_width} in frame at {scale}%: {display_pixels} px")
            dpi = round(display_pixels / frame_width,1)
            logging.debug(f"dpi of {filename} is: {dpi}")
            return dpi
    except Exception as err:
        logging.error(f"Error reading file {filename}: {err}")
    # TODO: check vertical DPI as well if provided


def get_original_dpi(filename):
    with Image(filename=filename) as img:
        return  img.resolution[0]
    

def scale_image(filename,scale, rename: bool = False):
    with Image(filename=filename) as img:
        new_width = round(img.width * scale)
        new_height = round(img.height * scale)
        logging.info(f"Resizing {Path(filename).name} from {img.width}x{img.height}px to {new_width}x{new_height}px")
        new_filename = f"{Path(filename).parent}/{Path(filename).stem}_resampled{Path(filename).suffix}"
        try:
            img.compression = "lzw"
            img.sample(new_width,new_height)
            # img.save(filename=new_filename)
            img.save(filename=filename)
        except Exception as err:
            logging.error(f"Error resampling {Path(filename).name}: {err}")


def compress_image(filename,method="lzw"):
    with Image(filename=filename) as img:
        logging.info(f"Compressing {Path(filename).name} using {method}")
        try:
            img.compression = method
            img.save(filename=filename)
        except Exception as err:
            logging.error(f"Error compressing {Path(filename).name}: {err}")


def get_images(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    images_used = {}

    image_frames = root.findall("./DOCUMENT/MASTEROBJECT[@PTYPE='2']") + root.findall("./DOCUMENT/PAGEOBJECT[@PTYPE='2']")
    for element in image_frames:
        image_file = Path(element.get('PFILE'))
        if image_file.suffix in {".pdf", ".eps"}:
            continue
        frame_width = float(element.get('WIDTH'))
        frame_height = float(element.get('HEIGHT'))
        x_scale = float(element.get('LOCALSCX'))
        y_scale = float(element.get('LOCALSCY'))
        image_dpi = get_dpi(f"{Path(filename).parent}/images/{image_file.name}",x_scale/PERCENT_TO_LOCAL_SC,frame_width*PTS_TO_INCHES,frame_height*PTS_TO_INCHES)
        image_frame = {"page": int(element.get('OwnPage'))+1, "width": frame_width, "height": frame_height, "dpi": image_dpi}
        if images_used.get(image_file.name):
            images_used[image_file.name].append(image_frame)
        else:
            images_used[image_file.name] = [image_frame]
    return images_used


def update_sla(filename,image_scales):
    tree = ET.parse(filename)
    root = tree.getroot()
    for element in root.findall("./DOCUMENT/MASTEROBJECT[@PTYPE='2']") + root.findall("./DOCUMENT/PAGEOBJECT[@PTYPE='2']"):
        if Path(element.get('PFILE')).name in image_scales:
            image = Path(element.get('PFILE')).name
            old_scale_x = float(element.get('LOCALSCX'))
            old_scale_y = float(element.get('LOCALSCY'))
            old_x = float(element.get('LOCALX'))
            old_y = float(element.get('LOCALY'))
            new_scale_x = old_scale_x/image_scales[image]
            new_scale_y = old_scale_y/image_scales[image]
            new_x = old_x * image_scales[image]
            new_y = old_y * image_scales[image]
            logging.info(f"Changing scale of {image} from {old_scale_x} to {new_scale_x}")
            logging.info(f"Changing X offset of {image} from {old_x} to {new_x}")
            element.set('LOCALSCX',str(new_scale_x))
            element.set('LOCALSCY',str(new_scale_y))
            element.set('LOCALX',str(new_x))
            element.set('LOCALY',str(new_y))

    tree.write(filename)


def optimise_file(filename):
    logging.info(f"\nOpening file: {filename}\n")
    images_used = get_images(filename)

    image_scales = {}
    for entry in images_used:
        lowest_dpi = round(sorted(images_used[entry],key=lambda x: x['dpi'])[0]['dpi'])
        logging.info(f"Image: {entry}\tInstances: {len(images_used[entry])}\tLowest DPI: {lowest_dpi}")
        
        if lowest_dpi > MAX_DPI and Path(entry).suffix in TYPES_TO_RESIZE:
            new_scale = TARGET_DPI/lowest_dpi
            image_scales[entry] = new_scale
            scale_image(Path(filename).parent/"images"/entry,new_scale)
        elif Path(entry).suffix in TYPES_TO_COMPRESS:
            compress_image(Path(filename).parent/"images"/entry)

    update_sla(filename,image_scales)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        optimise_file(sys.argv[1])
    else:
        print("Missing arguments: filename")
