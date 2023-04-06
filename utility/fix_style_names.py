import xml.etree.ElementTree as ET
import sys

STYLE_MAP = [
    (["header level 1", "header 1", "heading level 1", "heading 1"], "HEADER Level 1"),
    (["header level 2", "header 2", "heading level 2", "heading 2"], "HEADER Level 2"),
    (["toc1","toc level 1"], "TOC Level 1"),
    (["toc2","toc level 2"], "TOC Level 2"),
    (["toc rules"], "TOC Rules"),
    (["footer left", "footer - left"], "FOOTER Left"),
    (["footer right", "footer - right"], "FOOTER Right"),
]

def fix_styles(filename):
    
    style_dict = {}
    for entry in STYLE_MAP:
        for s in entry[0]:
            style_dict[s] = entry[1]

    # print(style_dict)

    tree = ET.parse(filename)
    root = tree.getroot()
    for element in root.findall('./DOCUMENT/STYLE'):
        old_name = element.get('NAME').lower()
        if old_name in style_dict:
            new_name = style_dict[old_name]
            element.set('PARENT', new_name)
            print(f"{element.get('NAME')} -> {new_name}")
        if element.get('PARENT'):
            p_name = element.get('PARENT').lower()
            if p_name in style_dict:
                element.set('PARENT', style_dict[p_name])
                print(f"PARENT: {p_name} -> {style_dict[p_name]}")
    tree.write(filename)


if __name__ == '__main__':
    fix_styles(sys.argv[1])
