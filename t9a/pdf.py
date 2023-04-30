'''Contains functions to analyse and manipulate both T9A slim rules PDFs and exported Full Army Books'''
import re
import os
import json
import logging
from pathlib import Path

from pypdf import PdfWriter, PdfReader
from py_pdf_parser.loaders import load_file


DEFAULT_FILENAME = r"D:\9th age\Scribus LABs\LAB_ID\images\T9A-FB_2ed_ID_2021_beta4_EN.pdf"

FONT_MAPPING = {
    r"\w{6}\+Caladea-(Bold|Regular),2\d*": "chapter_title",
}


def get_pages(filename):
    with open(filename, 'rb+') as pdf_file:
        pdf = PdfReader(pdf_file)
        return len(pdf.pages)


def parse_title(text):
    return re.sub(r' \(.+\)', '', text)
    # return text


def get_headings(filename, details=False, dump_json: bool = True):
    # TODO: check modified date on json v PDF to make sure it's up to date
    json_file = Path(filename).with_suffix(".json")
    if not Path(json_file).is_file():
        return parse_headings(filename, details, dump_json)
    with open(json_file) as json_content:
        return json.load(json_content)


def parse_headings(filename, details, dump_json):
    logging.info(f"Parsing {filename}")
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
    logging.info(entries)
    if dump_json:
        json_file = Path(filename).with_suffix(".json")
        with open(json_file,"w") as outfile:
            json.dump(entries,outfile,indent=4)

    return entries


def export_titles_to_json(pdf_file: str, json_file: str = ""):
    """Parses the titles from the given pdf file and creates a JSON file.

    Args:
        pdf_file (string): Full filename of rules PDF
        json_file (_type_, optional): Filename of JSON file to export. If none provided, file is created in same location as pdf_file.

    Returns:
        List of dictionaries of parsed titles
    """
    titles = get_headings(pdf_file,details=True)
    pdf_file = Path(pdf_file)
    if not json_file:
        json_file = Path(pdf_file).with_suffix('.json')
    with open(json_file,"w") as outfile:
        json.dump(titles,outfile,indent=4)
    return titles


def match_headings(pdf1, pdf2,details=False):
    pdf1_titles = get_headings(pdf1,details)
    logging.info(pdf1_titles)
    pdf2_titles = get_headings(pdf2,details)
    logging.info(pdf2_titles)
    return pdf1_titles == pdf2_titles


def compare_pdfs(pdf1, pdf2,details=False):
    pdf1_pagecout = get_pages(pdf1)
    pdf2_pagecount = get_pages(pdf2)

    pdf1_titles = get_headings(pdf1,details)
    pdf2_titles = get_headings(pdf2,details)
    print(pdf1_titles)
    print(pdf2_titles)
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

def add_bookmarks_to_pdf(filename, bookmarks, output_filename=None):
    with open(filename, 'rb+') as pdf_file:
        input_pdf = PdfReader(pdf_file)
        output = PdfWriter()
        
        output.clone_document_from_reader(input_pdf)
        output.add_metadata(input_pdf.metadata)
        output.page_mode = "/UseOutlines" # Show Bookmarks

    # TODO: Rewrite with recursion when my brain is less tired.

    l0_mark = None
    l1_mark = None
    l2_mark = None
    for mark in bookmarks:
        if int(mark['level']) == 0:
            l0_mark = output.add_outline_item(mark['text'], int(mark['page'])-1)
        elif mark['level'] == 1:
            l1_mark = output.add_outline_item(mark['text'], int(mark['page'])-1, l0_mark)
        elif mark['level'] == 2:
            l2_mark = output.add_outline_item(mark['text'], int(mark['page'])-1, l1_mark)
    
    ### Have to use a temporary file because input file apparantly needs to stay open while output is written, otherwise you get a blank file
    temp_file = f"{filename}.temp"
    with open(temp_file, 'wb') as pdf_file:
        output.write(pdf_file)

    if output_filename:
        try:
            os.remove(output_filename)
        except FileNotFoundError:
            pass
        os.rename(temp_file,output_filename)
    else:
        os.remove(filename)
        os.rename(temp_file, filename)