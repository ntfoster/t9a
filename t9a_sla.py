"""Contains methods for interacting with the .sla file for a 9th Age book"""

from pathlib import Path
import xml.etree.ElementTree as ET

VERSION_FRAME = "version_number"


class InvalidMarkException(Exception):
    pass

class LABfile:
    def __init__(self, filename):
        self.filename = filename
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()

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
                element.set("PFILE",new_pdf)
        if output_file:
            print(f'Writing to file: {output_file}')
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
        print(f"{self.filename}: Changed {current_version} to {version}")

    def get_embedded_rules(self):
        """Returns the full path of the embedded rules PDF

        Returns:
            Path: Full path to embedded rules PDF
        """        
        filepath = Path(self.filename)
        sla_dir = filepath.parent
        rules_layer = self.get_layer_number("Rules")
        element = self.root.find(f'./DOCUMENT/PAGEOBJECT[@LAYER="{rules_layer}"]')
        if element.get("PFILE")[-4:] == ".pdf":
            return sla_dir / Path(element.get("PFILE"))

    def parse_headers(self,style):
        """Scans file for text frames with given style applied and returns a list of entries with label, text, and page
        
        Args:
            style (string): Name of text style to scan for
        Returns:
            list: A list of {text:string, page:int} dictionaries
        """        

        entries = []
        for element in self.root.findall("./DOCUMENT/PAGEOBJECT[@PTYPE='4']"):
            page = int(element.get("OwnPage"))+1 # Scribus interal page numbers start at 0, so are 1 less than 'real' page numbers 
            for storytext in element:
                if page > 7: # after Contents page
                    is_header = False
                    for child in storytext:
                        if (
                            child.tag == "DefaultStyle"
                            and str(child.get("PARENT")).lower() == style.lower()
                        ):
                            is_header = True
                        if is_header:
                            text = None
                            if child.tag == "MARK":
                                label = child.get("label")
                                text = self.lookup_label(label)
                            elif child.tag == "ITEXT":
                                text = child.get("CH")
                            if text: 
                                entry = {"text": text, "page": page}
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
    

    def lookup_label(self,label):
        marks = self.root.find("./DOCUMENT/Marks")
        for mark in marks:
            if mark.get("type") == "3" and mark.get("label") == label:
                return mark.get("str")
        raise InvalidMarkException(f"{label} is not a valid Mark")
