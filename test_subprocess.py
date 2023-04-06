import subprocess
import sys
import os
from pathlib import Path
# print(sys.version)
# 
command = r'python "D:\9th age\t9a-scripts\t9a_pdf.py" "C:\Users\pusht\OneDrive\9th Age\Templates\LAB Template v2\images\t9a-fb_2ed_de_2023_beta1_en.pdf"'
command2 = r'python3 "D:\9th age\t9a-scripts\test_version.py"'

# subprocess.run(command2)
# print(os.getcwd())
# os.chdir(Path(__file__).parents[0])
current_env = os.environ.copy()
current_env['PYTHONPATH'] = ""
subprocess.run(command2,shell=True,env=current_env)

# os.system(command2)
