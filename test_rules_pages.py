import sys
from pathlib import Path

import scribus

from t9a.sla import SLAFile
from t9a.scribus import ScribusLAB


def main():
    sla = scribus.getDocName()
    lab = ScribusLAB()
    rules = lab.get_embedded_rules()
    rules_pages = lab.get_rules_pages()
    rules_page_count = rules_pages[1]-rules_pages[0]+1
    pdf_pages = int(scribus.valueDialog('Rules pagecount', 'How many pags are there in the embeddred rules PDF (total, including cover)?'))-1

    if rules_page_count == pdf_pages:
        result = f"Page counts match ({rules_page_count}). No modifications necessary"
    elif rules_page_count < pdf_pages:
        extra_pages = pdf_pages - rules_page_count
        result = f"Rules PDF has more pages ({pdf_pages}) than this document has allocated ({rules_page_count}: {lab.rules_start} - {lab.rules_end}). Extra pages required: {extra_pages}"
        pages_to_add = extra_pages + (extra_pages % 2) # need to add an extra if odd number.

        print(f"Getting items from page {lab.rules_end-1}")
        items = scribus.getAllObjects(type=scribus.ITEMTYPE_IMAGEFRAME, page=lab.rules_end-2, layer="Rules")
        print(items)
        rules_frame = items[-1]

        for _ in range(int(pages_to_add/2)):
            scribus.newPage(lab.rules_end,"A2 - Normal Right")
            scribus.newPage(lab.rules_end,"A1 - Normal Left")

        # Copy rules frame to new pages
        # scribus.copyObjects(rules_frame)
        # for i in range(extra_pages):
        #     scribus.gotoPage(i+1)
        #     scribus.pasteObjects()

    elif rules_page_count > pdf_pages:
        result = f"This document has more pages ({rules_page_count}) allocated to rules than the rules PDF ({pdf_pages}). Extra pages to remove: {rules_page_count - pdf_pages}"
        # remove extra pages
    scribus.messageBox("Pages",result)


if __name__ == "__main__":
    main()

