from pathlib import Path
import xml.etree.ElementTree as ET

VERSION_FRAME = "version_number"

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

