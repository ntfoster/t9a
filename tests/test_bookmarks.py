import sys
from pathlib import Path

from tabulate import tabulate

sys.path.append(str(Path(__file__).parents[1])) # needed to run from subdirectory
from t9a.pdf import add_bookmarks_to_pdf
from t9a.sla import SLAFile
from t9a_generate_labs import get_bookmarks

sla_file = Path(sys.argv[1])
input_pdf = sla_file.with_name(f"{sla_file.stem}_full_high.pdf")
output_pdf = input_pdf.with_name(f"{input_pdf.stem}_bookmarked.pdf")

lab = SLAFile(sla_file)

bookmarks = get_bookmarks(lab)
print(tabulate(bookmarks, tablefmt='simple'))

try:
    add_bookmarks_to_pdf(input_pdf,bookmarks,output_pdf)
except FileNotFoundError:
    print(f"File {input_pdf} doesn't exist. You may need to export it first.")

