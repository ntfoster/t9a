'''Contains functions to analyse Slim Rules PDFs'''
import re
import sys
import os
import json
from pathlib import Path
from py_pdf_parser.loaders import load_file


DEFAULT_FILENAME = r"D:\9th age\Scribus LABs\LAB_ID\images\T9A-FB_2ed_ID_2021_beta4_EN.pdf"

FONT_MAPPING = {
    r"\w{6}\+Caladea-(Bold|Regular),2\d*": "chapter_title",
}


def parse_title(text):
    return re.sub(r' \(.+\)', '', text)
    # return text


def get_titles(filename,details=False):
    doc = load_file(filename, font_mapping=FONT_MAPPING, font_mapping_is_regex=True)
    titles = doc.elements.filter_by_font("chapter_title")
    entries = []
    for index, item in enumerate(titles, start=1):
        title = parse_title(item.text())
        if title != "Changelog":
            entry = {}
            if details: 
                entry['order'] = index
            entry['title'] = title
            entry['page'] = item.page_number
            if details:
                entry['ypos'] = item.bounding_box.y1
            entries.append(entry)
    return entries


def export_titles_to_json(pdf_file: str, json_file: str = ""):
    """Parses the titles from the given pdf file and creates a JSON file.

    Args:
        pdf_file (string): Full filename of rules PDF
        json_file (_type_, optional): Filename of JSON file to export. If none provided, file is created in same location as pdf_file.

    Returns:
        List of dictionaries of parsed titles
    """
    titles = get_titles(pdf_file,details=True)
    pdf_file = Path(pdf_file)
    if not json_file:
        json_file = Path(pdf_file).with_suffix('.json')
    with open(json_file,"w") as outfile:
        json.dump(titles,outfile,indent=4)
    return titles


def match_titles(pdf1, pdf2,details=False):
    pdf1_titles = get_titles(pdf1,details)
    pdf2_titles = get_titles(pdf2,details)
    return pdf1_titles == pdf2_titles


def compare_pdfs(pdf1, pdf2,details=False):
    pdf1_titles = get_titles(pdf1,details)
    pdf2_titles = get_titles(pdf2,details)
    print(pdf1_titles, tablefmt="simple")
    print(pdf2_titles, tablefmt="simple")
    if pdf1_titles == pdf2_titles:
        print("Conents match!")
    else:
        print("Contents don't match!")


def get_version_from_PDF(pdf):
    filename = Path(pdf).stem
    # Examples:
    # t9a-fb_2ed_id_2021_beta2_en1.pdf
    # t9a-fb_2ed_wdg_2021_en.pdf
    # t9a_fb_2ed_id_2022_beta_1_hotfix_2_en.pdf
    # pdf_pattern = r"t9a-fb_2ed_[a-zA-Z]+_(\d{4})_?([a-zA-Z]+)?(\d+)?_\w{2}\.pdf"

    pdf_pattern = r"t9a[_|-]fb_2ed_[a-zA-Z]+_(\d{4})_?(beta_?\d)?_?(hotfix_?\d)?_\w{2}"
    pdf_re = re.compile(pdf_pattern, re.IGNORECASE)
    if not (result := pdf_re.match(filename)):
        raise ValueError(f"Filename '{filename}' was not in an expected format")
    version_list = [r for r in result.groups() if r]
    return " ".join(version_list)