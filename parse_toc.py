import xml.etree.ElementTree as ET
import csv
from pathlib import Path
import re
import argparse


background_toc_frame = 'TOC_Background'
rules_toc_frame = 'TOC_Rules'
header_style = 'HEADER Level 1'

root = None

# print(root.attrib)

def add_custom_labels(labels):
    custom_labels = [{"type":"General", "level":1, "label":"Cover", "page":1},{"type":"General", "level":1, "label":"Credits", "page":4}]
    labels.append(custom_labels)
    return labels

def get_page_from_mark(label):
    item_id = ''
    page = ''
    for element in root.findall(f'./DOCUMENT/Marks/Mark[@label="{label}"]'):
        item_id = element.get("ItemID")
    for element in root.findall(f'./DOCUMENT/PAGEOBJECT[@ItemID="{item_id}"]'):
        page = int(element.get("OwnPage"))+1
    return page

def parse_toc(frame): # scans text in the the given frame to build bookmarks
    toc_labels = []

    page_pattern = r"\d+"
    page_regex = re.compile(page_pattern)

    for element in root.findall(f"./DOCUMENT/PAGEOBJECT[@ANNAME='{frame}']/StoryText"):
        # para_style = "TOC level 1"
        level=1
        label = ""
        page = ""
        text = ""
        for child in element:
            if child.tag == "MARK":
                if child.get("type") == "3":
                    label = child.get("label")
                else:
                    page = get_page_from_mark(child.get("label"))
            if child.tag == "ITEXT":
                if page_regex.match( child.get("CH").lstrip() ):
                    page = child.get("CH").lstrip()
                elif child.get("CH") != " ":
                    text = child.get("CH")
            if child.tag == "para":
                para_style = child.get("PARENT")
                level = 2 if para_style == "TOC level 2" else 1
                clean_text = text.replace('\u00ad', '') # remove hidden soft hyphens
                entry = {"level":level, "label":label, "text":clean_text, "page":page}
                toc_labels.append(entry)
                label = ""
                page = ""
                text = ""
    # print(toc_labels)
    return toc_labels

def parse_headers(): # scans for 'HEADER Level 1' text to build bookmarks
    header_labels = []
    # for object in root.findall("./DOCUMENT/PAGEOBJECT/StoryText/DefaultStyle[@PARENT='HEADER Level 1']"):
    for element in root.findall(f"./DOCUMENT/PAGEOBJECT[@PTYPE='4']"):
        page = int(element.get("OwnPage"))+1 # Scribus interal page numbers start at 0, so are 1 less than 'real' page numbers 
        for storytext in element:
            is_header = False
            for child in storytext:
                if child.tag == "DefaultStyle":
                    if child.get("PARENT") == "HEADER Level 1":
                        is_header = True
                if is_header:
                    if child.tag == "MARK":
                        label = child.get("label")
                        entry = {"label":label, "text":"", "page":page}
                        header_labels.append(entry)
                    if child.tag == "ITEXT":
                        text = child.get("CH")
                        entry = {"label":"", "text":text, "page":page}
                        header_labels.append(entry)
    # print(header_labels)
    return header_labels

def lookup_labels(labels):
    marks = root.find("./DOCUMENT/Marks")
    for entry in labels:
        if entry["label"] != "":
            entry["text"] = entry["label"]
            for mark in marks:
                if mark.get("label") == entry["label"]:
                    entry["text"] = mark.get("str")

            
    return labels

def write_csv(entries,filename):
    with open(filename, "w", newline="", encoding='utf-8') as csvfile:
        fieldnames = ["level","text","page","children"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        # writer.writerows(entries)
        for entry in entries:
            if 'children' not in entry.keys():
                entry["children"] = 0
            writer.writerow({"level":entry["level"],"text":entry["text"],"page":entry["page"],"children":entry["children"]})
            # print(entry['type'])

def parse_contents(rules=True):
    # add same labels to front of every book
    custom_labels = [{"level":"0", "label":"Cover", "page":"1"},{"level":"0", "label":"Credits", "page":"4"}] #TODO: parameterise and split into function calls

    if not rules:
        labels_background = parse_toc(background_toc_frame)
        # need to make background headers top-level rather than children
        for label in labels_background:
            label["level"] = label["level"]-1
        labels = custom_labels + labels_background
    else:
        labels_background = parse_toc(background_toc_frame)
        background_count = len(labels_background)
        labels_rules = parse_toc(rules_toc_frame)
        rules_count = len(labels_rules)
        background_page = labels_background[0]["page"]
        rules_page = labels_rules[0]["page"]
        labels = custom_labels + [{"level":0, "label":"Background", "page":background_page, "children":background_count}] + labels_background + [{"level":0, "label":"Rules", "page":rules_page, "children":rules_count}] + labels_rules
    return lookup_labels(labels)

def parse_file(filename, rules=True):
    global root
    tree = ET.parse(filename)
    root = tree.getroot()
    return parse_contents(rules)


# if args.norules:
#     labels_background = parse_toc(background_toc_frame)
    
#     # need to make background headers top-level rather than children
#     for label in labels_background:
#         label["level"] = label["level"]-1
#     labels = custom_labels + labels_background
    
#     output = Path(input).stem+"_toc.csv" 
# else:
#     labels_background = parse_toc(background_toc_frame)
#     background_count = len(labels_background)
#     labels_rules = parse_toc(rules_toc_frame)
#     rules_count = len(labels_rules)
#     background_page = labels_background[0]["page"]
#     rules_page = labels_rules[0]["page"]
#     labels = custom_labels + [{"level":0, "label":"Background", "page":background_page, "children":background_count}] + labels_background + [{"level":0, "label":"Rules", "page":rules_page, "children":rules_count}] + labels_rules
#     output = Path(input).stem+"_toc.csv" 

# # for entry in labels:
# #     print(entry)
# entries = lookup_labels(labels)
# print(entries)
# write_csv(entries,output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="input .sla file")
    parser.add_argument('--norules', action='store_true', help="Don't parse Rules")
    args = parser.parse_args()

    rules = not args.norules
    if args.input:
        input = args.input
        parse_file(input,rules)





