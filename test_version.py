import sys
import os
print("----------------------------------------")

for entry in sys.path:
    if 'Scribus' in entry:
        sys.path.remove(entry)
# import py_pdf_parser
print(sys.version)
print("***************")
print(os.environ['PYTHONPATH'])
print("///////////////////////")

print(sys.path)
# print(py_pdf_parser.__file__)
