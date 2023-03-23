import sys

try:
    # Please do not use 'from scribus import *' . If you must use a 'from import',
    # Do so _after_ the 'import scribus' and only import the names you need, such
    # as commonly used constants.
    import scribus
except ImportError as err:
    print("This Python script is written for the Scribus scripting interface.")
    print("It can only be run from within Scribus.")
    sys.exit(1)

from pathlib import Path

# TODO: test that proper frames exist first

EXPECTED_FRAMES = ["rules_start", "rules_end", "epilogue_page", "edition", "version_number", "full_title", "norules_title", "nopoints_title", "rules_links"]

def test_frames():
    # pylint: disable=undefined-variable
    missing_frames = []
    try:
        scribus.deselectAll()
        for frame in EXPECTED_FRAMES:
            try:
                scribus.selectObject(frame)
            except:
                missing_frames.append(frame)
        if missing_frames:
            raise Exception(f"The following expected text frames are missing: {' ,'.join(missing_frames)}.")
    except Exception as err:
        scribus.messageBox("Missing frames", str(err), scribus.ICON_CRITICAL)

def load_titles_from_json(cls,filename):
    import json
    with open(filename) as json_file:
        return json.load(json_file)
        
class ScribusLAB:
    def __init__(self):
        test_frames()
        self.filename = scribus.getDocName()
        self.rules_start = int(scribus.getText('rules_start'))
        self.rules_end = int(scribus.getText("rules_end"))

    def remove_rules_headers(self):
        scribus.setActiveLayer('Notes')
        page = self.rules_start-1
        scribus.setRedraw(False)
        while page < self.rules_end:
            scribus.gotoPage(page)
            items = scribus.getAllObjects(4,page,'Notes')
            if len(items) > 0:
                for item in items:
                    scribus.deleteObject(item)
            page +=1

        scribus.setRedraw(True)

    def add_rules_headers(self,titles):
        scribus.setActiveLayer('Notes')
        for title in titles:
            page_number = title['page']+self.rules_start-2
            scribus.gotoPage(page_number)
            frame_name = title['title']+' Header'
            scribus.createText(56.58,841.89-title['ypos'],482,45,frame_name)
            scribus.setText(title['title'],frame_name)
            scribus.setParagraphStyle("HEADER Rules", frame_name)

    def get_rules_pages(self):
        rules_start = scribus.getAllText("rules_start")
        rules_end = scribus.getAllText("rules_end")
        return (int(rules_start),int(rules_end))

    def replace_pdf(self,new_pdf): # replaces linked rules pdf with '_nopoints' version
        # pdf_pattern = r".+\.(pdf)"
        # pdf_re = re.compile(pdf_pattern)
        page_range = self.get_rules_pages() 
        
        for i in range(page_range[0],page_range[1]+1):
            scribus.gotoPage(i)
            items = scribus.getPageItems()
            for item in items:
                scribus.deselectAll()
                if item[1] == 2: # if an image frame
                    file = scribus.getImageFile(item[0])
                    if file[-4:] == ".pdf":
                        # new_file = os.path.splitext(file)[0]+'_nopoints.pdf'
                        new_file = new_pdf
                        if Path(new_file).is_file():
                            scribus.loadImage(new_file,item[0])
                        else:
                            raise FileNotFoundError(f"Couldn't find file {new_file}")
    
    def replace_with_nopoints(self):
        current_pdf = None
        scribus.gotoPage(self.get_rules_pages[0])
        items = scribus.getPageItems()
        for item in items:
            scribus.deselectAll()
            if item[1] == 2: # if an image frame
                file = scribus.getImageFile(item[0])
                if file[-4:] == ".pdf":
                    current_pdf = file
        nopoints_pdf = Path(current_pdf).parents[0] / Path(current_pdf).stem + "_nopoints.pdf"
        if Path(nopoints_pdf).is_file():
            self.replace_pdf(nopoints_pdf)
