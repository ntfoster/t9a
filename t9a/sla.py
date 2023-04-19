"""Contains methods for interacting with the .sla file for a 9th Age Full/Legendary Army Book"""

from pathlib import Path
import xml.etree.ElementTree as ET
import logging

from t9a import EXPECTED_FRAMES, EXPECTED_STYLES, VERSION_FRAME


class InvalidMarkError(Exception):
    pass


class SLAFile:

    def __init__(self, filename):
        self.filename = filename
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()

    def test_frames(self,frames=EXPECTED_FRAMES):
        '''Tests if a list of frames is present in the document. If frames isn't specified, default list of expected frames is used.
        
        Args:
            frames ([string]): A list of frame names to test

        Returns:
            [string]: A list of missing frames    
        '''
        return [
            frame
            for frame in frames
            if self.root.find(f'./DOCUMENT/PAGEOBJECT[@ANNAME="{frame}"]') is None
        ]
    
    def test_styles(self, styles=EXPECTED_STYLES):
        """
        Tests if a list of styles exists in the document.

        Args:
            styles: A list of style names to test

        Returns:
            [string]: A list of missing styles
        """
        return [
            style
            for style in styles
            if self.root.find(f'./DOCUMENT/STYLE[@NAME="{style}"]') is None
        ]

    def get_layer_number(self,layer):
        """Returns layer number for the given layer name

        Args:
            layer (string): Layer name

        Returns:
            string: Layer number
        """        
        layer = self.root.find(f'./DOCUMENT/LAYERS[@NAME="{layer}"]')
        return layer.get("NUMMER")

    def replace_pdf(self,new_pdf,output_file=None):
        """Replaces embedded rules PDF with new one, optionally saving as a new file

        Args:
            new_pdf (string): Full path to new rules PDF
            output_file (string, optional): Full path to save new copy of file. Defaults to None.
        """        
        rules_layer = self.get_layer_number("Rules")
        for element in self.root.findall(f'./DOCUMENT/PAGEOBJECT[@LAYER="{rules_layer}"]'):
            if "PFILE" in element.attrib and element.get("PFILE")[-4:] == ".pdf":
                element.set("PFILE",str(new_pdf))
        if output_file:
            self.tree.write(output_file)
        else:
            self.tree.write(self.filename)

    def get_text(self,frame):
        """Get the text content from a specified text frame

        Args:
            frame (string): Frame name

        Returns:
            string: Content of text frame
        """
        # TODO: Get all text in cases of multiple ITEXT nodes
        element = self.root.find(f'./DOCUMENT/PAGEOBJECT[@ANNAME="{frame}"]')
        text_box = element.find('StoryText').find('ITEXT')
        return text_box.get('CH')

    def set_version(self,version):
        """Set version number text frame to new value

        Args:
            version (string): New version
        """
        element = self.root.find(f'./DOCUMENT/PAGEOBJECT[@ANNAME="{VERSION_FRAME}"]')
        version_text_box = element.find('StoryText').find('ITEXT')
        current_version = version_text_box.get('CH')
        version_text_box.set('CH', version)
        self.tree.write(self.filename)
        logging.info(f"{self.filename}: Changed {current_version} to {version}")

    def get_embedded_rules(self):
        """Returns the full path of the embedded rules PDF

        Returns:
            Path: Full path to embedded rules PDF
        """        
        sla_dir = Path(self.filename).parent
        rules_layer = self.get_layer_number("Rules")
        element = self.root.find(f'./DOCUMENT/PAGEOBJECT[@LAYER="{rules_layer}"]')
        if element.get("PFILE")[-4:] == ".pdf":
            return sla_dir / Path(element.get("PFILE"))

    def parse_headers(self,styles):
        """Scans file for text frames with given style applied and returns a list of entries with label, text, and page
        
        Args:
            styles (string): A list of text styles to scan for
        Returns:
            list: A list of {text:string, page:int} dictionaries
        """        
        # TODO: Parse styles applied at text-level as well as frame-level.
        entries = []
        for element in self.root.findall("./DOCUMENT/PAGEOBJECT[@PTYPE='4']"):
            page = int(element.get("OwnPage"))+1 # Scribus interal page numbers start at 0, so are 1 less than 'real' page numbers 
            for storytext in element:
                if page > 7: # after Contents page
                    is_header = False
                    for child in storytext:
                        if (
                            child.tag == "DefaultStyle"
                            and str(child.get("PARENT")).lower() in [x.lower() for x in styles]
                        ):
                            is_header = True
                        if is_header:
                            text = None
                            if child.tag == "MARK":
                                label = child.get("label")
                                text = self.lookup_variable_text(label)
                            elif child.tag == "ITEXT":
                                text = child.get("CH")
                            if text: 
                                entry = {"text": text, "page": page}
                                entries.append(entry)
        return sorted(entries, key=lambda k: k['page'])

    def parse_headers_multilevel(self, style_map):
        """Scans file for text frames with given style applied and returns a list of entries with label, text, and page
        
        Args:
            style_map: A list of (int,string) tuples of TOC level and style name. E.g. [(1,"HEADER Level 1"),(2,"HEADER Level 2")]
        Returns:
            list: A list of {"level": int, "text":string, "page":int} dictionaries
        """
        # TODO: Parse styles applied at text-level as well as frame-level.
        entries = []
        for element in self.root.findall("./DOCUMENT/PAGEOBJECT[@PTYPE='4']"):
            # Scribus interal page numbers start at 0, so are 1 less than 'real' page numbers
            page = int(element.get("OwnPage"))+1
            for storytext in element:
                if page > 7:  # after Contents page
                    is_header = False
                    for child in storytext:
                        if (
                            child.tag == "DefaultStyle"
                            # and str(child.get("PARENT")).lower() in [x[1].lower() for x in style_map]
                        ):
                            for style in style_map:
                                if str(child.get("PARENT")).lower() == style[1].lower():
                                    is_header = True
                                    level = style[0]
                        if is_header:
                            text = None
                            if child.tag == "MARK":
                                label = child.get("label")
                                text = self.lookup_variable_text(label)
                            elif child.tag == "ITEXT":
                                text = child.get("CH")
                            if text:
                                entry = {"level":level,"text": text, "page": page}
                                entries.append(entry)
        return sorted(entries, key=lambda k: k['page'])


    def lookup_labels(self,labels):
        marks = self.root.find("./DOCUMENT/Marks")
        for entry in labels:
            if entry["label"] != "":
                entry["text"] = entry["label"]
                for mark in marks:
                    if mark.get("type") == "3" and mark.get("label") == entry["label"]:
                        entry["text"] = mark.get("str")

        return labels

    def lookup_variable_text(self,label):
        """Lookup text value of Variable Text mark

        Args:
            label (str): Label of Variable Text mark

        Raises:
            InvalidMarkError: No mark with the given label could be found

        Returns:
            str: Value of the Variable Text mark
        """
        try:
            return self.root.find(f"./DOCUMENT/Marks/Mark[@label='{label}']").get('str')
        except:
            raise InvalidMarkError(f"{label} is not a valid Mark")
    
    def parse_headers_from_text_sla(self,header_styles):
        """Searches every text frame for test formatted with the given styles and returns list of corresponding headings

        Args:
            header_styles ([str]): List of style names in hierarchical order (e.g. ["HEADER Level 1", "HEADER Level 2"])

        Returns:
            dict[level,text,page]: list of {"level":int, "text":str, "page":int} header entries
        """
        headers = []
        elements = sorted(self.root.findall("./DOCUMENT/PAGEOBJECT[@PTYPE='4']"), key=lambda e: (int(e.get("OwnPage")), float(e.get("YPOS"))))

        for element in elements:
            page = int(element.get("OwnPage"))+1

            if page <= 7: # before or on Contents page
                continue

            for storytext in element:
                text = None
                style = None
                frame_style = None
                
                s = iter(storytext)
                for child in s:

                    if child.tag == "DefaultStyle" and child.get("PARENT") is not None:
                        frame_style = style = child.get("PARENT")
                    elif child.tag in ["MARK","ITEXT"]:
                        if child.tag == "MARK":
                            text = self.lookup_variable_text(child.get("label"))
                        else:
                            text = child.get("CH")

                        while child.tag in ["MARK","breakline","ITEXT"]:
                            child = next(s)
                            if child.tag == "ITEXT":
                                text += child.get("CH")
                            elif child.tag == "breakline":
                                text += " "
                            elif child.tag in ["para","trail"]:
                                style = child.get("PARENT") or frame_style

                    if text and style in header_styles:
                        level = header_styles.index(style)+1
                        headers.append({"level":level,"text": text, "page": page})
                        frame_style = style = None
                        text = None
        return headers

    def check_nopoints(self):
        """Checks if nopoints version of the embedded rules PDF exists in the correct folder

        Returns:
            bool: True if file exists, else False
        """
        rules = self.get_embedded_rules()
        nopoints = rules.with_name(f"{rules.stem}_nopoints.pdf")
        return Path(nopoints).is_file()


