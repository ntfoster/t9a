'''Contains methods to manipulate T9A Army Books in Scribus'''
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
import re
import json
import logging

import t9a
# from t9a import EXPECTED_STYLES, EXPECTED_FRAMES
from t9a.sla import SLAFile

#####################
### FOOTER CONFIG ###
#####################
# in MM
Y_POS_MIN = 280
FOOTER_X_LOCS = [19, 20, 23, 116] # for removing footers
FOOTER_Y_LOCS = [280, 281, 282, 283, 284, 285, 286, 287, 288, 289] # for removing footers

FOOTER_X_POS = 20
FOOTER_Y_POS = 284.5
FOOTER_WIDTH = 70
FOOTER_HEIGHT = 7

# Unique mesasurements for certain books
UD_FOOTER_X_POS_ODD = 115.5
UD_FOOTER_X_POS_EVEN = 23
UD_FOOTER_Y_POS = 282.58

SE_FOOTER_X_POS = 20
SE_FOOTER_Y_POS = 280.84

############################
### TOC HYPERLINK CONFIG ###
############################
BACKGROUND_TOC_FRAME = "TOC_Background"
RULES_TOC_FRAME = "TOC_Rules"

FRAME_WIDTH = 81
FRAME_HEIGHT = 5.35
FRAME_GAP = 1.00
OFFSET = -1.00

CONTENTS_PAGE = 7

UD_SE_FRAME_WIDTH = 71 # UD/SE books have narrower contents frames


def test_frames():
    # pylint: disable=undefined-variable
    missing_frames = []
    try:
        scribus.deselectAll()
        for frame in t9a.EXPECTED_FRAMES:
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
    

def get_master_page(string):
    master_pages = scribus.masterPageNames()
    for page in master_pages:
        if page.startswith(string):
            return page


def get_footer_pos():
    master_page = get_master_page("A1")
    scribus.editMasterPage(master_page)
    items = scribus.getAllObjects(4)
    for item in items:
        x,y = scribus.getPosition(item)
        if y >= Y_POS_MIN:
            scribus.closeMasterPage()
            return(round(y,1))
    scribus.closeMasterPage()

        
class ScribusLAB:
    def __init__(self):
        logging.debug("Creating ScribusLAB")
        self.filename = scribus.getDocName()
        self.lab = SLAFile(self.filename)
        self.rules_start = int(scribus.getText('rules_start'))
        self.rules_end = int(scribus.getText("rules_end"))
        logging.debug("Getting Footer Y position")
        self.footer_y_pos = get_footer_pos() or FOOTER_Y_POS
        logging.debug(f"Footer Y Position: {self.footer_y_pos}")
        logging.debug("Finished creating ScribusLAB")

    def test_styles(self):
        doc_styles = scribus.getParagraphStyles()
        missing_styles = [style for style in t9a.EXPECTED_STYLES if style not in doc_styles]
        if missing_styles:
            return(missing_styles)

    def remove_rules_headers(self):
        current_layer = scribus.getActiveLayer()
        scribus.setActiveLayer('Notes')
        page = self.rules_start-1
        scribus.setRedraw(False)
        while page < self.rules_end:
            scribus.gotoPage(page)
            items = scribus.getAllObjects(4,page,'Notes') # 4 = text frame
            if len(items) > 0:
                for item in items:
                    if scribus.isLocked(item):
                        scribus.lockObject(item)
                    scribus.deleteObject(item)
            page += 1
        scribus.setRedraw(True)
        scribus.setActiveLayer(current_layer)
        scribus.docChanged(True)

    def load_titles_from_json(self,filename):
        with open(filename) as json_file:
            return json.load(json_file)

    def add_rules_headers(self,titles):
        current_units = scribus.getUnit()
        scribus.setUnit(scribus.UNIT_POINTS)
        scribus.setActiveLayer('Notes')
        for title in titles:
            page_number = title['page']+self.rules_start-2
            scribus.gotoPage(page_number)
            # frame_name = title['title']+' Header'
            frame_name = scribus.createText(56.58,841.89-title['ypos'],482,45)
            scribus.setText(title['title'],frame_name)
            scribus.setParagraphStyle(t9a.HEADER_RULES, frame_name)
        scribus.setUnit(current_units)
        scribus.docChanged(True)


    def get_rules_pages(self):
        rules_start = int(scribus.getAllText("rules_start"))
        rules_end = int(scribus.getAllText("rules_end"))
        return(rules_start,rules_end)

    def get_embedded_rules(self):
        items = scribus.getAllObjects(
            type=scribus.ITEMTYPE_IMAGEFRAME, page=self.rules_start-1, layer="Rules")
        for item in items:
            filename = scribus.getImageFile(item)
            if filename[-4:] == ".pdf":
                return filename
            else:
                raise FileNotFoundError

    def replace_pdf(self,new_pdf): # replaces linked rules pdf with '_nopoints' version
        # pdf_pattern = r".+\.(pdf)"
        # pdf_re = re.compile(pdf_pattern)
        page_range = self.get_rules_pages() 
        scribus.setRedraw(False)
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
        scribus.setRedraw(True)
        scribus.docChanged(True)

    
    def replace_with_nopoints(self):
        current_pdf = self.get_embedded_rules()
        nopoints_pdf = Path(current_pdf).with_suffix("_nopoints.pdf")
        if Path(nopoints_pdf).is_file():
            self.replace_pdf(nopoints_pdf)


    def set_toc_frame(self,frame, headers, style_map):
        # TODO: adjust size of frame based on number of headers
        text = ""
        char_count = 0
        # if 2 in [h['level'] for h in headers]:
        #     print("We've got an L2!")
        header_details = []
        for i,entry in enumerate(headers):
            header_detail = (i,char_count,entry['level'],entry['text'],entry['page'])
            char_count += len(entry['text']) + len(str(entry['page'])) + 2
            # print(header_detail)
            header_details.append(header_detail)
            # print(f"{i}:{entry['level']} - ({len(entry['text'])+len(str(entry['page']))+2}) {entry['text']},{entry['page']}")
        # selectFrameText(19, 1, "TOC_Background")
        # setParagraphStyle("TOC level 2", "TOC_Background")
        for entry in headers:
            line = f'{entry["text"]}\t{entry["page"]}\n'
            text += line
        scribus.setText(text, frame)
        try:
            scribus.setParagraphStyle(style_map[0][1], frame)
        except scribus.NotFoundError:
            scribus.messageBox("Style Not Found",f"Couldn't find style {style_map[0][1]}")
        scribus.layoutText(frame)
        for entry in header_details:
            if entry[2] > 1:
                scribus.selectFrameText(entry[1],1,frame)
                try:
                    scribus.setParagraphStyle(style_map[entry[2]-1][1], frame)
                except scribus.NotFoundError:
                    scribus.messageBox("Style Not Found",
                                    f"Couldn't find style {style_map[0][1]}")
        scribus.docChanged(True)

    def get_frame_headings_by_style(self,frame,page_number,heading_styles):
        headings = []
        scribus.deselectAll()
        scribus.selectObject(frame)
        paragraphs = scribus.getFrameText().split('\r')
        # print(paragraphs)
        start = 0
        for p in paragraphs:
            scribus.selectFrameText(start, len(p))
            p_style = scribus.getParagraphStyle()
            if p_style is None:
                start += len(p) + 1
                continue
            if p_style in heading_styles:
                headings.append({
                    'level': heading_styles.index(p_style)+1,
                    'text': p,
                    'page': page_number,
                })
            start += len(p) + 1
        # scribus.deselectAll()
        return headings

    def parse_headings_frames(self,page_range,heading_styles):
        headings = []
        # scribus.deselectAll()
        for page in page_range:
            scribus.gotoPage(page)
            frames = scribus.getAllObjects(4) # 4 = text frame
            # print(f"Page: {page}, Frames: {frames}")
            for frame in frames:
                h = self.get_frame_headings_by_style(frame,page,heading_styles)
                if h:
                    # print(f"Page: {page}, Frame: {frame}")
                    # print(h)
                    headings.extend(h)
        # print("----------\n\n")
        return headings


    def create_toc(self,background=True,rules=True):
        if background:
            # background_headers = self.lab.parse_headers_multilevel([(1,t9a.HEADER1), (2,t9a.HEADER2)])
            background_headers = self.parse_headings_frames(range(8,scribus.pageCount()),[t9a.HEADER1,t9a.HEADER2])
            self.set_toc_frame("TOC_Background", background_headers, [(1,t9a.TOC1),(2,t9a.TOC2)])
        if rules:
            rules_headers = self.lab.parse_headers_multilevel([(1,t9a.HEADER_RULES)])
            self.set_toc_frame("TOC_Rules", rules_headers, [(1,t9a.TOC_RULES)])
        scribus.docChanged(True)

    def create_toc_from_sla(self,background=True, rules=True):
        if background:
            background_headers = self.lab.parse_headers_from_text_sla([t9a.HEADER1,t9a.HEADER2])
            logging.debug(f"Background headers: {background_headers}")
            self.set_toc_frame("TOC_Background", background_headers, [(1,t9a.TOC1),(2,t9a.TOC2)])
        if rules:
            rules_headers = self.parse_headings_frames(range(self.rules_start,self.rules_end),[t9a.HEADER_RULES])
            logging.debug(f"Rules headers: {rules_headers}")
            self.set_toc_frame("TOC_Rules", rules_headers, [(1,t9a.TOC_RULES)])
        scribus.docChanged(True)

    def remove_footers(self):
        """Removes running footer text frames from pre-determined postion on every page"""
        page = 5 # start at contents page
        scribus.setRedraw(False)
        scribus.setUnit(scribus.UNIT_MM)

        while page < scribus.pageCount():
            scribus.gotoPage(page)
            # items = scribus.getPageItems()
            items = scribus.getAllObjects(4,layer="Hyperlinks")
            # logging.debug(f"Page {page}: {items}")
            for item in items:
                pos = scribus.getPosition(item)
                # if round(pos[0]) == 20 and round(pos[1]) == 286:
                if round(pos[0]) in FOOTER_X_LOCS and round(pos[1]) in FOOTER_Y_LOCS:
                # if round(pos[0]) in [20, 23, 116] and pos[1] // 10 == 28:
                    if scribus.isLocked(item):
                        scribus.lockObject(item)
                    scribus.deleteObject(item)
            page += 1

        scribus.setRedraw(True)
        scribus.docChanged(True)

    def create_footer(self, page, footer, x=FOOTER_X_POS, y=FOOTER_Y_POS, w=FOOTER_WIDTH, h=FOOTER_HEIGHT):
        scribus.gotoPage(page)
        # y = self.footer_y_pos
        label = scribus.createText(
            x, y, w, h)
        scribus.setText(footer, label)

        try: # try different style names
            scribus.setStyle(t9a.FOOTER_L, label)
        except scribus.NotFoundError:
            scribus.messageBox(
                "Style Error", f"Couldn't find appropriate Footer style: {t9a.FOOTER_L}")
            sys.exit()
        scribus.docChanged(True)

    def create_footer_UD(self, page, footer):
        scribus.gotoPage(page)
        if page % 2 == 0:  # even, left-hand page
            label = scribus.createText(
                UD_FOOTER_X_POS_EVEN, UD_FOOTER_Y_POS, FOOTER_WIDTH, FOOTER_HEIGHT)
            scribus.setText(footer, label)
            try:
                scribus.setStyle(t9a.FOOTER_L, label)
            except scribus.NotFoundError:
                scribus.messageBox(
                    "Style Error", "Couldn't find appropriate Footer style: 'FOOTER left'")
                return
        else:  # odd, right-hand page
            label = scribus.createText(
                UD_FOOTER_X_POS_ODD, UD_FOOTER_Y_POS, FOOTER_WIDTH, FOOTER_HEIGHT)
            scribus.setText(footer, label)
            try:
                scribus.setStyle(t9a.FOOTER_R, label)
            except scribus.NotFoundError:
                scribus.messageBox(
                    "Style Error", "Couldn't find appropriate Footer style: 'FOOTER right'")
                return
        scribus.docChanged(True)

    def set_footers(self):
        self.remove_footers()
        background_headers = self.lab.parse_headers_from_text_sla([t9a.HEADER1])
        rules_headers = self.parse_headings_frames(range(self.rules_start,self.rules_end),[t9a.HEADER_RULES])
        headers = background_headers + rules_headers
        pages = range(8, scribus.pageCount())

        scribus.setUnit(scribus.UNIT_MM)
        scribus.setRedraw(False)
        current_layer = scribus.getActiveLayer()
        scribus.setActiveLayer("Hyperlinks")
        current_header = ""
        for page in pages:
            # don't create footer on page with "blank" master
            if scribus.getMasterPage(page).startswith("X"):
                continue

            for x in headers:
                if x["page"] == page:
                    current_header = x["text"]
            if "_UD_" in scribus.getDocName():
                self.create_footer_UD(page, current_header)
            elif "_SE_" in scribus.getDocName():
                self.create_footer(page, current_header, SE_FOOTER_X_POS, SE_FOOTER_Y_POS)
            else:
                self.create_footer(page, current_header, y=self.footer_y_pos)
        scribus.setActiveLayer(current_layer)
        scribus.setRedraw(True)
        scribus.docChanged(True)

    def delete_toc_hyperlinks(self):
        current_layer = scribus.getActiveLayer()
        scribus.setRedraw(False)
        logging.info("Deleting hyperlinks")
        logging.debug(f"Going to page: {CONTENTS_PAGE}")
        scribus.gotoPage(CONTENTS_PAGE)
        scribus.setActiveLayer("Hyperlinks")
        links = scribus.getAllObjects(page=CONTENTS_PAGE-1,layer="Hyperlinks")
        logging.debug(f"Links: {links}")
        if links:
            try:
                linkgroup = scribus.groupObjects(links)
                scribus.deleteObject(linkgroup)
            except Exception as err:
                logging.error(err)
        
        # if links:
        #     scribus.deselectAll()
        #     for link in links:
        #         logging.debug(f"Deleting link: {link}")
        #         if scribus.isLocked(link):
        #                 scribus.lockObject(link) # unlock
        #         logging.debug(f"Selecting: {link}")
        #         scribus.selectObject(link)
        # logging.debug(f"Selected objects: {scribus.selectionCount()}")
        # scribus.deleteObject()
        scribus.setRedraw(True)
        scribus.setActiveLayer(current_layer)
        scribus.docChanged(True)
        logging.debug("Finished deleting hyperlinks")

    def create_hyperlinks(self, frame, prefix):
        # TODO: Handle multi-line entries

        scribus.setUnit(scribus.UNIT_MM)
        scribus.gotoPage(CONTENTS_PAGE)
        
        
        def get_toc_entries(frame):
            text = scribus.getAllText(frame)
            paragraphs = text.split('\r')
            pattern = r'.+\t(\d+)'
            regex = re.compile(pattern)
            pages = []
            for p in paragraphs:
                result = regex.match(p)
                if result:
                    pages.append(result[1])
            return pages

        pages = get_toc_entries(frame)
        i = 0
        half = int((len(pages)+1)/2)
        frame_pos = scribus.getPosition(frame)
        x_pos = frame_pos[0]
        y_pos = frame_pos[1]+OFFSET
        scribus.setActiveLayer("Hyperlinks")
        links = []
        
        filename = scribus.getDocName()
        if "_UD_" in filename or "_SE_" in filename:
            hyperlink_width = UD_SE_FRAME_WIDTH
        else:
            hyperlink_width = FRAME_WIDTH
        while i < len(pages):
            if i == half:
                x_pos = 109
                y_pos = frame_pos[1]+OFFSET  # reset y coord for right column

            frame_name = prefix+str(i+1)
            new_frame = scribus.createText(x_pos, y_pos, hyperlink_width,
                            FRAME_HEIGHT, frame_name)
            # logging.debug(f"Setting annotation {new_frame} to page {int(pages[i])}")
            scribus.setLinkAnnotation(int(pages[i]), 0, 0, new_frame)
            # scribus.lockObject(frame_name)
            links.append(frame_name)
            i += 1
            y_pos = y_pos + FRAME_HEIGHT + FRAME_GAP
        if prefix == "bh":
            try:
                scribus.setItemName("bh_epilogue", frame_name)
                links[-1] = "bh_epilogue"
            except UnboundLocalError as err:
                pass
        scribus.docChanged(True)
        return links

    def create_toc_hyperlinks(self):
        current_layer = scribus.getActiveLayer()
        self.delete_toc_hyperlinks()
        background_links = self.create_hyperlinks(BACKGROUND_TOC_FRAME, 'bh')
        # logging.debug(background_links)
        # group = scribus.groupObjects(background_links)
        # scribus.setItemName("background_links", group)
        rules_links = self.create_hyperlinks(RULES_TOC_FRAME, 'rh')
        group = scribus.groupObjects(rules_links)
        scribus.setItemName("rules_links", group)
        scribus.setActiveLayer(current_layer)
        scribus.docChanged(True)

    def check_nopoints(self):
        """Checks if nopoints version of the embedded rules PDF exists in the correct folder

        Returns:
            bool: True if file exists, else False
        """
        rules = Path(self.get_embedded_rules())
        nopoints = rules.with_name(f"{rules.stem}_nopoints.pdf")
        return Path(nopoints).is_file()

