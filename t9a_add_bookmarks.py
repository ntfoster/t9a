from pypdf import PdfWriter, PdfReader
import os

def add_bookmarks(filename, bookmarks):
    with open(filename, 'rb+') as pdf_file:
        input = PdfReader(pdf_file)
        output = PdfWriter()

        output.clone_document_from_reader(input)
        output.add_metadata(input.metadata)
        output.page_mode = "/UseOutlines" # Show Bookmarks

        parent = None
        for mark in bookmarks:
            if mark['level'] == 0:
                # Top level bookmark 
                parent = output.add_outline_item(mark['text'], int(mark['page'])-1)
            else:
                # Child bookmarks
                output.add_outline_item(mark['text'], int(mark['page'])-1, parent)

    ### Have to use a temporary file because input file apparantly needs to stay open while output is written, otherwise you get a blank file
        temp_file = f"{filename}.temp"
        with open(temp_file, 'wb') as pdf_file:
            output.write(pdf_file)
    os.remove(filename)
    os.rename(temp_file, filename)
