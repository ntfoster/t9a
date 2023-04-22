import sys
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from wand.image import Image

sys.path.append(str(Path(__file__).parents[1])) # needed to run from subdirectory
from optimise_images import optimise_file, get_original_dpi
from lab_manager import get_sla_files


logging.basicConfig(level=logging.ERROR)

def list_original_dpis(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    for element in root.findall("./DOCUMENT/PAGEOBJECT[@PTYPE='2']"):
        image_file = Path(filename).parent/Path(element.get('PFILE'))
        if image_file.suffix in [".eps",".pdf"]:
            continue
        print(f"{element.get('PFILE')}: {get_original_dpi(image_file)} DPI")

sla_files = get_sla_files()

for file in sla_files[3:]:
    print(f"Opening file: {file}")
    optimise_file(file.replace("Scribus LABs","Scribus LABs optimised"))
